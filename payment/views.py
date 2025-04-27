import stripe
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework.views import APIView

from client.request.functions import get_plan
from Dashboard.auth.functions import validate_user_id
from Dashboard.bot.functions import deactivate_bots
from Dashboard.emails import spripe_error_email
from Dashboard.management.commands.check_sub_days import cancel_stripe_sub
from Dashboard.models import UserModel
from Dashboard.payment.functions import check_payment_data
from Dashboard.payment.models import StripePaymentStatus, StripeSession, Stripe, StarterPlan, BasicPlan, PremiumPlan

import time
from typing import Union


def get_unix_time():
    return int(time.time()) + 1800


class Template(TemplateView):
    template_name = "emaiil.html"


# todo stripe terms of use einbinden sodass user bestätigen kann das die abrechnugnimmer nach genau 30 tagen erfolgt -> chekcamrks
# @permission_classes([IsAuthenticated])
class Checkout(APIView):
    # permission_classes = [IsAuthenticated]

    def get_session_metadata(self, user_id):
        return {
            "payment_id": user_id
        }

    def create_stripe_cus(self, user):
        print("CREATE NEW STRIPE CUSTOMER...")
        cus = stripe.Customer.create(
            email=user.email,
        )
        stripe_cus = cus.id
        print("NEW CREATED CUSTOMER ID:", stripe_cus)
        return stripe_cus

    def create_stripe_object(self, plan_type, session_id, customer_id) -> Stripe or None:
        try:
            print("CREATE THE STRIPE OBJECT...")

            session_status = StripePaymentStatus.objects.create()
            print("STRIPE STATUS OBJECT CREATED...")

            stripe_session = StripeSession.objects.create(
                status=session_status,
                requested_service=plan_type,
                session_id=session_id
            )
            print("STRIPE SESSION OBJECT CREATED...")

            stripe_model = Stripe.objects.create(
                customer_id=customer_id
            )
            stripe_model.sessions.add(stripe_session)
            stripe_model.save()
            print("STRIPE OBJECT CREATED AND SAVED...")

            return stripe_model
        except Exception as e:
            print("ERROR CREATING THE STRIPE INSTANCES:", e)

    def check_user_stripe_object(self, data: list, session_id: str, customer_id: str):
        print("CHECK FOR EXISTING STRIPE USER OBJECT")
        user = data[1]
        if not user.stripe_payments:
            print("NO STRIPE ACCOUNT FOUND...")
            stripe_model = self.create_stripe_object(data[0], session_id, customer_id)
            if not stripe_model:
                print("ERROR AT SAVING THE STRIPE INSTANCE...")
                return {
                    "status_code": 85,
                    "message": "Stripe instances couldn't be created",
                }
            print("NEW STRIPE INSTANCE CREATED, ADD TO THE USER MODEL")
            user.stripe_payments = stripe_model
            user.stripe_payments.save()
            user.save()
        else:
            print("EXISTING STRIPE USER ACCOUND MODEL FOUND...")
            if not user.stripe_payments.customer_id:
                print("ADD THE NEW CREATED CUSTOMER ID...")
                user.stripe_payments.customer_id = customer_id
                user.stripe_payments.save()
            print("UPDATE STRIPE SESSION . . .")
            stripe_status = StripePaymentStatus.objects.create()
            new_session = StripeSession.objects.create(
                session_id=session_id,
                status=stripe_status,
                requested_service=data[0],
            )
            user.stripe_payments.sessions.add(new_session)

    def get_price_id_test(self, plan_type, duration):
        if plan_type == "Starter":
            if duration == "annual":
                return "price_1P4L9ULeVm9hIlTcUf5sMROV"  # 99€
            else:
                return "price_1P4L0lLeVm9hIlTcVAHXodfY"  # 9€
        elif plan_type == "Basic":
            if duration == "annual":
                return "price_1P40IbLeVm9hIlTc8fAhJ3Kv"  # 270€
            else:
                return "price_1P28LeLeVm9hIlTcHhNS7vKV"  # 26€
        elif plan_type == "Premium":
            if duration == "annual":
                return "price_1P4LBcLeVm9hIlTcfNjcCd2Q"  # 549€
            else:
                return "price_1P2G8VLeVm9hIlTc3GDPyGTW"  # 54€

    def get_price_id_prod(self, plan_type, duration):
        if plan_type == "Starter":
            if duration == "annual":
                return "price_1PO2iDLeVm9hIlTccuPTEM41"  # 99€
            else:
                return "price_1PO2iELeVm9hIlTcYTnyGCHy"  # 9€
        elif plan_type == "Basic":
            if duration == "annual":
                return "price_1PO2iELeVm9hIlTcezNvhokL"  # 270€
            else:
                return "price_1PO2iELeVm9hIlTcnXDFlZH6"  # 26€
        elif plan_type == "Premium":
            if duration == "annual":
                return "price_1PO2iDLeVm9hIlTcXZq5fU69"  # 549€
            else:
                return "price_1PO2iELeVm9hIlTc7NzyF7lL"  # 54€

    def get_stripe_cus_id(self, user):
        print("GET STRIPE CUS ID--------------------------------------------------------------------------------------")
        stripe_cus = None
        if user.stripe_payments:
            print("STRIPE PAYMENT OBJECT FOUND...")
            if user.stripe_payments.customer_id:
                stripe_cus = user.stripe_payments.customer_id
                print("... WITH CUS ID:", stripe_cus)
                try:
                    print("CHECK EXISTING CUS ID FOR AN EXISITNG STRIPE USER...")
                    customer = stripe.Customer.retrieve(stripe_cus)
                    print("CUSTOMER FROM ID AT STRIPES SIDE FOUND:", customer)
                    if not customer or customer and customer.get("deleted"):
                        print("CUSTOMER ID NOT FOUND ON STRIPE, CREATING A NEW CUSTOMER...")
                        stripe_cus = self.create_stripe_cus(user)
                        user.stripe_payments.customer_id = stripe_cus
                        user.stripe_payments.save()
                        print("CUSTOMER SUCCESSFUL CREATED ON STRIPE...")
                except stripe.error.InvalidRequestError:  # -> invalid params
                    # If the customer doesn't exist, create a new one
                    print("CUSTOMER ID NOT FOUND ON STRIPE, CREATING A NEW CUSTOMER...")
                    stripe_cus = self.create_stripe_cus(user)
                    user.stripe_payments.customer_id = stripe_cus
                    user.stripe_payments.save()
                    print("CUSTOMER SUCCESSFUL CREATED ON STRIPE...")
                except stripe.error.APIConnectionError as e:
                    print("SERVERSIDE CONNECTION ERROR OCCURRED:", e)
                    return {
                        "status_code": 94,
                        "message": "Serverside network error occurred."
                    }

                except stripe.error.APIError as e:
                    print("STRIPE API ERROR OCCURRED:", e)
                    return {
                        "status_code": 83,
                        "message": "Serverside network error occurred."
                    }

                except Exception as e:
                    print("UNEXPECTEF ERROR OCCURRED:", e)
                    return {
                        "status_code": 83,
                        "message": "Serverside network error occurred."
                    }
        else:
            print("CREATE A NEW STRIPE CUSTOMER")
            stripe_cus = self.create_stripe_cus(user)
        return stripe_cus

    def post(self, request, *args, **kwargs):
        """
        :param request:
        {
            "planType": "Starter", "Premium", "Basic",
            "user_id": str,
            "duration": "monthly" | "annual"
        }
        :return:
        success:
        {
            "status_code": 200,
            "id": checkout_session.id,
            "checkout_session_url": checkout_session.url
        }
        fail:
        {
            "status_code": 83,
            "message": "Session could not be created"
        }
        user.stripe_payments.customer_id = customer.id
            user.stripe_payments.save()
        """
        print("Checkout-----------------------------------------------------------------------------------------------")
        data: list = check_payment_data(request)  # [plan_type, user, duration]
        if isinstance(data, dict):
            return JsonResponse(data)

        duration = data[2]
        user: UserModel = data[1]
        plan_type = data[0]

        stripe_cus = self.get_stripe_cus_id(user)
        if not stripe_cus:
            return JsonResponse(
                {
                    "status_code": 83,
                    "message": "Session could not be created"
                }
            )
        elif isinstance(stripe_cus, dict):
            return JsonResponse(stripe_cus)
        try:
            print("BEGIN CHECKOUT SESSION CREATION WITH CUSTOMER ID:", stripe_cus if stripe_cus else None)
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card", "link", "paypal"],
                customer=stripe_cus,
                after_expiration={
                    "recovery": {
                        "enabled": True,
                        "allow_promotion_codes": False,
                    }
                },
                automatic_tax={
                    "enabled": False,  # Enables,
                },
                allow_promotion_codes=True,
                billing_address_collection="auto",  # or required
                currency="eur",
                client_reference_id=data[1].user_id,  # auth id to reconcile stripe session with my system
                consent_collection={
                    "terms_of_service": "none"  # user need to confirm tos  required
                },

                expires_at=get_unix_time(),  # when the session will exp -> in sec, unix format
                locale="auto",  # language tag from the session -> auto = brtowsersetting
                line_items=[
                    {
                        "price": self.get_price_id_prod(plan_type, duration),
                        "quantity": 1
                    }
                ],
                ui_mode="hosted",  # or embedded
                mode="subscription",
                success_url="https://www.botworld.cloud/payment-success",
                cancel_url="https://www.botworld.cloud/payment-failed",  # todo
                metadata={
                    "user_id": user.user_id,
                    "duration": duration
                }
            )

            print("CHECKOUT SESSION CREATED")
            print(f"CHECKOUT SESSION ID: {checkout_session.id}")
            print(f"CHECKOUT SESSION URL: {checkout_session.url}")
            print(f"CHECKOUT SESSION CUSTOMER: {checkout_session.customer}")

            # update the Model

            response = self.check_user_stripe_object(
                data,
                checkout_session.id,
                customer_id=stripe_cus
            )
            if response and isinstance(response, dict):
                return JsonResponse(response)

            return JsonResponse(
                {
                    "status_code": 200,
                    "checkout_session_url": checkout_session.url
                }
            )
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            print('Status is: %s' % e.http_status)
            print('Code is: %s' % e.code)
            # param is '' in this case
            print('Param is: %s' % e.param)
            print('Message is: %s' % e.user_message)
        except stripe.error.RateLimitError as e:
            print("RATE LIMIT OCCURRED:", e)
            return JsonResponse(
                {
                    "status_code": 95,
                    "message": "Too many requests. Please try again later."
                }
            )
        except stripe.error.InvalidRequestError as e:
            print("INVLID PARAMS TRANSFERED TO STRIPE ERROR:", e)

        except stripe.error.AuthenticationError as e:
            print("AUTHENTICATION ERROR OCCURRED:", e)
            spripe_error_email(error=e, email=user.email, user_id=user.user_id, plus_sub="(AuthenticationError)")

        except stripe.error.APIConnectionError as e:
            print("APIConnectionError OCCURRED:", e)
            return JsonResponse(
                {
                    "status_code": 94,
                    "message": "Serverside network error occurred."
                }
            )
        except stripe.error.StripeError as e:
            print("STRIPE ERROR OCCURRED:", e)
            spripe_error_email(error=e, email=user.email, user_id=user.user_id)

        except Exception as e:
            print("ERROR OCCURRED BECAUSE ERROR:", e)

        return JsonResponse(
            {
                "status_code": 83,
                "message": "Session could not be created"
            }
        )


class Unsubscribe(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        print("UNSUBSCRIBE REQUEST====================================================================================")
        user_id = request.data.get('user_id')
        print("USER ID RECEIVED:", user_id)

        user: Union[UserModel, None] = validate_user_id(request=None, uid=user_id)
        if not user:
            return JsonResponse({
                "status_code": 21,
                "message": "Authentication request error. Please contact the support",
            }
            )

        try:
            if user.subscription:
                print("user.stripe_payments.subscription_id", user.stripe_payments.subscription_id)
                user.subscription.status = "INACTIVE"
                user.subscription.save()
                print("TRY CANCEL THE SUBSCRIPTION...")

            deactivate_bots(user)
            cancel_stripe_sub(user)

            plan = get_plan(user)
            if isinstance(plan, StarterPlan):
                print("DELETE STARTER SUBSCRITION...")
                user.subscription.starter = None
                user.subscription.save()

            elif isinstance(plan, BasicPlan):
                print("DELETE BASIC SUBSCRITION...")
                user.subscription.basic = None
                user.subscription.save()

            elif isinstance(plan, PremiumPlan):
                print("DELETE PREMIUM SUBSCRITION...")
                user.subscription.premium = None
                user.subscription.save()

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            print('Status is: %s' % e.http_status)
            print('Code is: %s' % e.code)
            # param is '' in this case
            print('Param is: %s' % e.param)
            print('Message is: %s' % e.user_message)
        except stripe.error.RateLimitError as e:
            print("RATE LIMIT OCCURRED:", e)
            return JsonResponse(
                {
                    "status_code": 83,
                    "message": "Too many requests. Please try again later."
                }
            )

        except stripe.error.InvalidRequestError as e:
            print("INVLID PARAMS TRANSFERED TO STRIPE ERROR:", e)

        except stripe.error.AuthenticationError as e:
            print("AUTHENTICATION ERROR OCCURRED:", e)
            spripe_error_email(error=e, email=user.email, user_id=user.user_id, plus_sub="(AuthenticationError)")

        except stripe.error.APIConnectionError as e:
            print("APIConnectionError OCCURRED:", e)
            return JsonResponse(
                {
                    "status_code": 83,
                    "message": "Serverside network error occurred."
                }
            )
        except stripe.error.StripeError as e:
            print("STRIPE ERROR OCCURRED:", e)
            spripe_error_email(error=e, email=user.email, user_id=user.user_id)


        except Exception as e:
            print("ERROR:", e)
            return JsonResponse({
                "status_code": 87,
                "message": "Serverside error. please contact the support.",
            })
        return JsonResponse({
            "status_code": 200,
            "message": "Successfull unsubscribed from the plan.",
        })


"""
#discounts={
                    "coupon": ""
                    # todo coolen discount code überlegen -> othe field = promotion -> just one can be added
                },
                
                
                
AUTOMATED DISCOUNT
discounts=[
                    {
                        "promotion_code": "promo_1P7dxnLeVm9hIlTcWEfaHyXg"
                    }
                ],
"""

from datetime import datetime

import stripe

from client.request.functions import get_plan, check_sub_fields
from Dashboard.emails import unable_delete_old_stripe_payment_email, unable_receive_sub_id_from_payment, \
    stripe_webhook_payment_success_data_email, spripe_error_email
from Dashboard.google_stuff.send_mail.process import gmail_send_message
from Dashboard.google_stuff.send_mail.texts import get_email
from Dashboard.models import UserModel
from Dashboard.payment.models import PremiumPlan, Stripe, StarterPlan, BasicPlan, SubscriptionModel
from chat_bot_webite.settings import DEV_EMAIL


def delete_current_plan(user):
    plan = get_plan(user)
    if plan:
        print("CURRENT USER PLAN:", plan.name)
        subscription = user.subscription

        # Identify which plan to clear based on the instance type
        if isinstance(plan, StarterPlan):
            subscription.starter = None

        elif isinstance(plan, BasicPlan):
            subscription.basic = None

        elif isinstance(plan, PremiumPlan):
            subscription.premium = None

        subscription.status = "INACTIVE"
        # Save the subscription after clearing the reference
        subscription.save()
        print("DELETE PREVIOUS PLAN...")


def get_user_stripe_webhook(event):
    try:
        customer = event.data.object["customer"]
        print("CUSTOMER RECEIVED:", customer)
        stripe_model = Stripe.objects.get(customer_id=customer)
        print("STRIPE MODEL FROM GIVEN CUSTOMER FOUND:", stripe_model)

        user = UserModel.objects.get(stripe_payments=stripe_model)
        print("LINKED USER TO THAT MODEL FOUND:", user)
        return user
    except Exception as e:
        print("COULD NOT GET THE USER CAUSE ERROR:", e)


################################################################### INVOICE SUCCESS

from django.db import transaction


# Configure your logger
# logger = logging.getLogger(__name__)


def check_delete_old_sub(user, event):
    old_sub_id = user.stripe_payments.subscription_id if user.stripe_payments.subscription_id else ""
    print("CURRETN SUB ID: ", old_sub_id)
    new_sub_id = event.data.object["subscription"]
    if not new_sub_id:
        unable_receive_sub_id_from_payment(user)
        return

    print(f"RECEIVED SUB ID: {new_sub_id}")
    print(f"EXISTING SUB ID: {old_sub_id}")

    if not old_sub_id or len(old_sub_id) == 0:
        print("NO CURRENT SUB ID FOUND, UPDATE...")  # todo SUCCESSFUL PAYMET FOM BESTTEST TRIGGERS THIS?
        user.stripe_payments.subscription_id = new_sub_id
        user.stripe_payments.save(update_fields=["subscription_id"])
        return
    elif old_sub_id == new_sub_id:
        print("ALERT!!! OLD SUB ID == NEW SUB ID ...")
        return

    try:

        print("Attempt to DELETE the CURRENT subscription")
        # https: // docs.stripe.com / billing / subscriptions / cancel?dashboard - or -api = api & lang = python

        sub = stripe.Subscription.retrieve(old_sub_id)
        if sub and not sub["deleted"]:
            print("CANCELLING...")
            stripe.Subscription.cancel(old_sub_id)
        else:
            print("UNABLE TO CANCEL BECAUSE SUB ID DOES NOT EXIST a stripe...")
    except stripe.error.StripeError as e:
        print(f"ERROR OCCURRED CANNOT CANCEL THE SUB: {e}")
        # Send an email notification on failure
        unable_delete_old_stripe_payment_email(user, old_sub_id, new_sub_id, str(e))
        return

    print("Save new subscription ID")
    try:
        with transaction.atomic():
            user.stripe_payments.subscription_id = new_sub_id
            user.stripe_payments.save(update_fields=["subscription_id"])
            print("NEW SUB ID SAVED IN USER MODEL")

    except Exception as e:
        print(f"DATABASE UPDATE FAILED: {e}")
        return "FAILED DATABASE"


def invoice_success_process(event):
    # todo check f user has disabled bots ( maybe he has downgreaded -> bots was disabled -> now he upgrade again -> enable bots
    try:
        print("COLLECTING DATA...")
        user = get_user_stripe_webhook(event)

        product_data = event.data.object["lines"]
        print("PRODUCT DATA ARRAY:", product_data)

        price_id = product_data.data[0].plan.id
        print("PRICE ID:", price_id)

        invoice_url = event.data.object.invoice_pdf
        print("INVOICE URL:", invoice_url)

        if not user.subscription:
            print("USER HAS NO SUBSCRIPTION MODEL CREATE ONE...")
            subscription = SubscriptionModel.objects.create()
            user.subscription = subscription
            user.save()

        # CHECK ALL SUBS FIELDS
        check_sub_fields(user)

        create_plan_model_prod(
            price_id=price_id,
            user=user,
        )

        # CHECK THE EXISTING SUB ID FOR CASE A USER HAS UP- DOWNGREADED ITS PLAN SO I NEED TO STOP THE PAYMENT FOR THE
        # OLD PLAN
        check_delete_old_sub(user, event) # TODO CANCEL CHECK'

        print("UPDATED PLAN SUCCESSFULY, SEND EMAILS")
        invoice_success_email(user.email, invoice_url, product_data)
        stripe_webhook_payment_success_data_email(event)
        user.subscription.status = "ACTIVE"
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

    except stripe.error.InvalidRequestError as e:
        print("INVLID PARAMS TRANSFERED TO STRIPE ERROR:", e)

    except stripe.error.AuthenticationError as e:
        print("AUTHENTICATION ERROR OCCURRED:", e)
        spripe_error_email(error=e, email=user.email, user_id=user.user_id, plus_sub="(AuthenticationError)")

    except stripe.error.APIConnectionError as e:
        print("APIConnectionError OCCURRED:", e)

    except stripe.error.StripeError as e:
        print("STRIPE ERROR OCCURRED:", e)
        spripe_error_email(error=e, email=user.email, user_id=user.user_id)


    except Exception as e:
        print("ERROR WHILE CREATING THE INSTANCES:", e)

    def get_price_id_prod(self, plan_type, duration):
        if plan_type == "Starter":
            if duration == "annual":
                return ""  # 99€
            else:
                return ""  # 9€
        elif plan_type == "Basic":
            if duration == "annual":
                return ""  # 270€
            else:
                return "price_1PO2iELeVm9hIlTcnXDFlZH6"  # 26€
        elif plan_type == "Premium":
            if duration == "annual":
                return "price_1PO2iDLeVm9hIlTcXZq5fU69"  # 549€
            else:
                return "price_1PO2iELeVm9hIlTc7NzyF7lL"  # 54€


def create_plan_model_prod(price_id, user):
    try:
        if price_id == "price_1PO2iELeVm9hIlTcYTnyGCHy" or price_id == "price_1PO2iDLeVm9hIlTccuPTEM41":  # Starter ID todo
            user_add_starter(
                user=user,
                annual=price_id == "price_1PO2iDLeVm9hIlTccuPTEM41",
            )

        elif price_id == "price_1PO2iELeVm9hIlTcnXDFlZH6" or price_id == "price_1PO2iELeVm9hIlTcezNvhokL":  # Basic ID todo
            user_add_basic(
                user=user,
                annual=price_id == "price_1PO2iELeVm9hIlTcezNvhokL",
            )

        elif price_id == "price_1PO2iELeVm9hIlTc7NzyF7lL" or price_id == "price_1PO2iDLeVm9hIlTcXZq5fU69":  # Premium todo
            user_add_premium(
                user=user,
                annual=price_id == "price_1PO2iDLeVm9hIlTcXZq5fU69",
            )
        else:
            print("NO PRICE ID MATCHED...")
    except Exception as e:
        print("CREATE PLANS FAILED CAUSE ERROR:", e)




def create_plan_model_test(price_id, user):
    try:
        if price_id == "price_1P4L0lLeVm9hIlTcVAHXodfY" or price_id == "price_1P4L9ULeVm9hIlTcUf5sMROV":  # Starter ID todo
            user_add_starter(
                user=user,
                annual=price_id == "price_1P4L9ULeVm9hIlTcUf5sMROV",

            )

        elif price_id == "price_1P28LeLeVm9hIlTcHhNS7vKV" or price_id == "price_1P40IbLeVm9hIlTc8fAhJ3Kv":  # Basic ID todo
            user_add_basic(
                user=user,
                annual=price_id == "price_1P40IbLeVm9hIlTc8fAhJ3Kv",

            )

        elif price_id == "price_1P2G8VLeVm9hIlTc3GDPyGTW" or price_id == "price_1P4LBcLeVm9hIlTcfNjcCd2Q":  # Premium todo
            user_add_premium(
                user=user,
                annual=price_id == "price_1P4LBcLeVm9hIlTcfNjcCd2Q",

            )
        else:
            print("NO PRICE ID MATCHED...")
    except Exception as e:
        print("CREATE PLANS FAILED CAUSE ERROR:", e)


def check_enable_bots(value: int, user: UserModel) -> int:
    """
    Adjusts the activation status of the user's bots based on their plan.
    Activates up to 'value' bots, and deactivates the rest.
    :param value: Total number of bots the plan includes.
    :param user: UserModel instance.
    :return: Number of additional bots the user can activate.
    """
    remaining_slots = value
    print("INITIAL VALUE:", value)
    if user.bots.exists():
        all_user_bots = user.bots.all().order_by('created_at')

        # Determine the number of bots to activate and deactivate
        total_bots = all_user_bots.count()
        bots_to_activate = min(value, total_bots)
        bots_to_deactivate = total_bots - bots_to_activate

        # Activate the first 'n' bots TODO DOUBLE CHECK
        for bot in all_user_bots[:bots_to_activate]:
            if bot.status == "FAILED" or bot.status == "IN_PROGRESS" or bot.status == "RETRY":
                pass
            elif bot.status == "F_INACTIVE":
                bot.status = "FAILED"
            elif bot.status == "P_INACTIVE":
                bot.status = "IN_PROGRESS"
            else:
                bot.status = "ACTIVE"
            bot.save()

        # Deactivate the remaining bots, if any
        if bots_to_deactivate > 0:
            for bot in all_user_bots[bots_to_activate:]:
                if bot.status == "FAILED":
                    bot.status = "F_INACTIVE"

                elif bot.status == "IN_PROGRESS":
                    bot.status = "P_INACTIVE"
                elif bot.status == "RETRY":
                    bot.status = "R_INACTIVE"
                else:
                    bot.status = "INACTIVE"

                bot.save()

        # Calculate the remaining slots for new bots
        remaining_slots = value - bots_to_activate
        print("DECREASED FROM", value, "TO", remaining_slots)
    return remaining_slots


def user_add_starter(user, annual):
    print("STARTER PLAN INVOICE PAID...")
    if not user.subscription.starter:
        starter = StarterPlan.objects.create(
            days_left=32 if not annual else 366,
            status="ACTIVE",
            total_bots=check_enable_bots(1, user)
        )
        print("UPGRADING TO STARTER...")

        # DELETE THE EXISTING PLAN
        delete_current_plan(user)

        user.subscription.starter = starter
        user.subscription.starter.save()
        user.subscription.save()
        print("NEW USER PLAN:", user.subscription.starter.name)

        gmail_send_message(
            user.email,
            get_email(
                heading="",
                body_heading=f"Congratulations and thank you for subscribing to our Starter Plan!",
                body_text=f"""Your subscription has been activated, and you now have full 
                          access to all the features and benefits that are available to starter's.
                          
                          What you can do now: <br /> 
                          <a
                          href="https://botworld.cloud/dashboard"
                          style="color: #4b5563;"
                          alt="Create your first bot">
                          Create your first bot
                        </a> <bt />
                          <a
                          href="https://botworld.cloud/supported-platforms"
                          style="color: #4b5563;"
                          alt="Guides">
                          Explore our guides
                        </a> <bt />
                        
                        Have Fun! """

            ),
            f"STARTER PLAN ACTIVE!"
        )
    else:
        print("UPDATING EXISTING STARTER PLAN...")
        user.subscription.starter.status = "ACTIVE"  # todo in chat check's mit einbauen
        user.subscription.starter.days_left = 32 if not annual else 366
        user.subscription.starter.monthly_chats = 500
        user.subscription.starter.save()


def user_add_premium(user, annual):
    print("PREMIUM PLAN INVOICE PAID...")
    if not user.subscription.premium:
        premium = PremiumPlan.objects.create(
            days_left=32 if not annual else 366,
            status="ACTIVE",
            total_bots=check_enable_bots(5, user)
        )
        print("UPGRADING TO PREMIUM...")

        # DELETE THE EXISTING PLAN
        delete_current_plan(user)

        user.subscription.premium = premium
        user.subscription.premium.save()
        user.subscription.save()
        print("NEW USER PLAN:", user.subscription.premium.name)

        gmail_send_message(
            user.email,
            get_email(
                heading="",
                body_heading=f"Congratulations and thank you for subscribing to our Premium Plan!",
                body_text=f"""Your subscription has been activated, and you now have full 
                                  access to all the features and benefits that are available to premium member's.

                                  What you can do now: <br /> 
                                  <a
                                  href="https://botworld.cloud/dashboard"
                                  style="color: #4b5563;"
                                  alt="Create your first bot">
                                  Create your first bot
                                </a> <bt />
                                  <a
                                  href="https://botworld.cloud/supported-platforms"
                                  style="color: #4b5563;"
                                  alt="Guides">
                                  Explore our guides
                                </a> <bt />

                                Have Fun! """

            ),
            f"PREMIUM PLAN ACTIVE!"
        )
    else:
        print("UPDATING EXISTING PREMIUM PLAN...")
        user.subscription.premium.status = "ACTIVE"  # todo in chat check's mit einbauen
        user.subscription.premium.days_left = 32 if not annual else 366
        user.subscription.premium.monthly_chats = 5000
        user.subscription.premium.save()


def user_add_basic(user, annual):
    print("BASIC PLAN INVOICE PAID...")
    if not user.subscription.basic:
        basic = BasicPlan.objects.create(
            days_left=32 if not annual else 366,
            status="ACTIVE",
            total_bots=check_enable_bots(2, user)  # BOTS WILL BE ACTIVATED HERE
        )
        print("UPGRADING TO BASIC...")

        # DELETE THE EXISTING PLAN
        delete_current_plan(user)

        user.subscription.basic = basic
        user.subscription.basic.save()
        user.subscription.save()
        print("NEW USER PLAN:", user.subscription.basic.name)

        gmail_send_message(
            user.email,
            get_email(
                heading="",
                body_heading=f"Congratulations and thank you for subscribing to our Basic Plan!",
                body_text=f"""Your subscription has been activated, and you now have full 
                              access to all the Base plan features and benefits.

                              What you can do now: <br /> 
                              <a
                              href="https://botworld.cloud/dashboard"
                              style="color: #4b5563;"
                              alt="Create your first bot">
                              Create your first bot
                            </a> <bt />
                              <a
                              href="https://botworld.cloud/supported-platforms"
                              style="color: #4b5563;"
                              alt="Guides">
                              Explore our guides
                            </a> <bt />

                            Have Fun! """

            ),
            f"BASIC PLAN ACTIVE!"
        )

    else:
        print("UPDATING EXISTING BASIC PLAN...")
        user.subscription.basic.status = "ACTIVE"  # todo in chat check's mit einbauen
        user.subscription.basic.days_left = 32 if not annual else 366
        user.subscription.basic.monthly_chats = 2000
        user.subscription.basic.save()


def invoice_success_email(email, invoice_url, product_data):
    gmail_send_message(
        email,
        get_email(
            heading="",
            body_heading=f"""<span style='font-weight : bold;'>Thanks for your purchase!</span>""",
            body_text=f"""You can download the invoice of your subscription 
                            <a
                              href="{invoice_url}"
                              style="color: #4b5563;"
                              alt="Guides">
                              here
                            </a>.
                            """

        ),
        f"Here comes your BotWorld invoice"
    )


"""

 def create_sub_process(self, session_id, user, duration):
        print("CREATE THE SUBSCRIPTION INSTANCES...")
        try:
            user_stripe_session = user.stripe_payments.sessions.get(session_id=session_id)

            if user_stripe_session.requested_service == "BASIC":
                basic_plan = BasicPlan.objects.create(
                    days_left=30 if duration == "monthly" else 365,
                )

                user.subscription.basic = basic_plan
                user.subscription.starter.delete()
                user.subscription.save()

            elif user_stripe_session.requested_service == "PREMIUM":
                premium_plan = PremiumPlan.objects.create(
                    days_left=30 if duration == "monthly" else 365,
                )

                user.subscription.premium = premium_plan
                user.subscription.starter.delete()
                user.subscription.save()

            user_stripe_session.status.status_id = "SUCCESS"
            user_stripe_session.status.save()
            user_stripe_session.save()
            gmail_send_message(
                user.email,
                success_sub(),
                f"Subscription successfully!"
            )

            return True

        except Exception as e:
            print("COULDN'T CREATE THE SUB INSTANCES CAUSE THE FOLLOWING ERROR:", str(e))
            
"""


######################################################################## INVOICE FAILED
def invoice_failed_process(event):
    """
    Will be every time called when a payment failed OR a checkout session will be cancelled.


    Case: user has Basic and want to switch to premium but the payment failed -> do not delete the plans here lol!
    Case 2: User has An active plan and the automated sub fee failed -> days will be reduced,
    at 0 the plan will be del automatically
    """

    print("UPDATE THE SU MODELS...")
    user = get_user_stripe_webhook(event)

    gmail_send_message(
        DEV_EMAIL,
        get_email(
            heading="Unfortunately A payment has been failed",
            body_heading=f"""Hi,""",
            body_text=f"""
            Unfortunately we could not register a successful payment at this time for the following erven: \n 
            {event}
            time: {datetime.time()}
            
            Think that's an issue? Please contact us while answer to this email.
            """
        ),
        "USER Payment Failed this time"
    )


def delete_sub_process(event):
    print("UNSUBSCRIBE THE USER FROM SUBSCRIPTION...")
    user = get_user_stripe_webhook(event)

    if user.subscription.starter:
        user.subscription.starter.status = "DELETED"

    elif user.subscription.basic:
        user.subscription.basic.status = "DELETED"

    elif user.subscription.premium:
        user.subscription.premium.status = "DELETED"

    elif user.subscription.custom:
        user.subscription.custom.status = "DELETED"

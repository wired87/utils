import stripe
from django.http import HttpResponse
from rest_framework.views import APIView

from Dashboard.google_stuff.send_mail.process import gmail_send_message
from Dashboard.google_stuff.send_mail.texts import get_email
from Dashboard.models import UserModel
from Dashboard.payment.webhook_functions import invoice_success_process, invoice_failed_process
from chat_bot_webite.settings import STRIPE_ENDPOINT_SECRET_PRODUCTION


# TODO: DECREASE EVERY DAY for every user "days_left" -1

class PaymentMessage(APIView):

    def save_customer_id(self, user_id, session_id, payment_methods: list, customer_id, invoice_id):
        print("UPDATE CUSTOMER MODELS...")
        user = None
        try:
            user = UserModel.objects.get(user_id=user_id)
            print("USER SET...")
            stripe_session = user.stripe_payments.sessions.filter(session_id=session_id)
            print("STRIPE SESSION OBJECT CREATED")
            # UPDATE THE SESSION FIELDS
            stripe_session.payment_method = [(method, ",") for method in payment_methods]
            stripe_session.invoice_id = invoice_id
            stripe_session.save()

            print("STRIPE SESSION UPDATED")
            # ADD CUSTOMER ID
            if not user.stripe_payments.customer_id:
                user.stripe_payments.customer_id = customer_id
                user.stripe_payments.save()
                print("CUSTOER SAVED...")
        except Exception as e:
            print("COULD NOT UPDATE THE SESSION MODELS CAUSE ERROR:", e)
            if user:
                gmail_send_message(
                    user.email,
                    get_email(
                        heading="Here comes your reset url",
                        body_heading=f"""Please dont share the url with anybody.""",
                        body_text=f"""For the next 30 min you can reset your password
                                            """
                    ),
                    "Forgot your password?")


    def post(self, request, *args, **kwargs):
        print("STRIPE WEBHOOK EVENT TRIGGERED...")

        payload = request.body
        print("DATA RECEIVED:", payload)

        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        print("SIG:", sig_header)
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_ENDPOINT_SECRET_PRODUCTION
            )
            print("EVENT CREATED:", event)

        except ValueError as e:
            # Invalid payload
            print('Error parsing payload: {}'.format(str(e)))
            return HttpResponse(status=400)

        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            print('Error verifying webhook signature: {}'.format(str(e)))
            return HttpResponse(status=400)

        if event.type == "invoice.payment_succeeded":
            # FULL OBJECT CAN BE FOUND HERE: https://docs.stripe.com/api/invoices/object
            print("SUCCESSFUL PAYMENT DETECTED...")
            # stripe_webhook_payment_success_data_email(event)
            invoice_success_process(
                event=event
            )

        elif event.type == "invoice.payment_failed":
            # FULL OBJECT CAN BE FOUND HERE: https://docs.stripe.com/api/invoices/object
            print("FAILED PAYMENT DETECTED...")
            invoice_failed_process(event)

        elif event.type == 'customer.subscription.updated':
            pass  # todo

        else:
            print('Unhandled event type {}'.format(event.type))

        return HttpResponse(status=200)




"""
        if event.type == 'checkout.session.completed':
            print("CHECKOUT SESSION COMPLETED...")

     
            User has chose a plan and has finished the checkout process
            The response will include a session object https://docs.stripe.com/api/checkout/sessions/object
            1. get the metadata user id
            2. get the session_id
            3. get user
            4. u
        

            user_id = event.data.object["metadata"]["user_id"]
            print("USER ID FOUND:", user_id)
            session_id = event.data.object["id"]
            print("SESSION ID FOUND:", user_id)
            payment_methods = event.data.object["payment_method_types"]
            print("PAYMENT METHODS:", user_id)
            customer_id = event.data.object["customer"]
            print("CUSTOMER FOUND:", user_id)

            self.save_customer_id(
                user_id=user_id,
                session_id=session_id,
                payment_methods=payment_methods,
                customer_id=customer_id
            )

        el

"""
from Dashboard.auth.functions import validate_user_id
from Dashboard.models import UserModel
from Dashboard.payment.models import *
import stripe
from typing import Union, Dict, List

from chat_bot_webite.settings import STRIPE_PROD_API_KEY

# This is your test secret API key.
stripe.api_key = STRIPE_PROD_API_KEY


def get_plan_model(plan_type):
    if plan_type == "basic":
        return BasicPlan.objects.create()

    elif plan_type == "premium":
        return PremiumPlan.objects.create()


"""
@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': '{{PRICE_ID}}',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
            automatic_tax={'enabled': True},
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)
"""

def check_payment_data(request) -> Union[Dict[str, Union[int, str]], List[Union[str, UserModel]]]:
    print("CHECKING PAYMENT DATA...")
    plan_type = request.data.get('planType')
    if not plan_type or not isinstance(plan_type, str) or plan_type not in ["Starter", "Premium", "Basic"]:
        print("PLAN TYPE NOT VALID...")
        return {
            "status_code": 81,
            "message": "Invalid plan type"
        }

    duration = request.data.get('duration')  # annual, monthly
    if not duration or not isinstance(duration, str) or duration not in ["annual", "monthly"]:
        print("DURATION TYPE NOT VALID...")
        return {
            "status_code": 86,
            "message": "Invalid duration"
        }
    user_id = request.data.get('user_id')
    print("USER ID RECEIVED:", user_id)

    user: Union[UserModel, None] = validate_user_id(request=None, uid=user_id)
    if not user:
        return {
            "status_code": 21,
            "message": "Authentication request error. Please contact the support",
        }

    p_data = [plan_type, user, duration]
    print("PAYMENT DATA COLLECTED:", p_data)
    return p_data


"""
@receiver(post_save, sender=UserModel)
def create_user_payment(user, created, **kwargs):
    if created:
        payment = PaymentProcess.objects.create(

        )
        user.payments.add(payment)
"""

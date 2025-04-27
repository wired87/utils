from django.db import models



# SUBSCRIPTION PLANS
def starter_pros():
    return {
        "items": [
            "No Code builder",
            "1 ChatBot",
            "20 Chats",
            "1 automated Tuning process",
            "Unlimited Websites"
        ]
    }

def basic_pros():
    return {
        "items": [
            "No Code builder",
            "2 ChatBot's",
            "2000 Chats",
            "1 automated monthly Tuning process",
            "Unlimited Websites",
        ]
    }


def premium_pros():
    return {
    "items": [
        "No Code builder",
        "4 ChatBot's",
        "6000 Chats",
        "Unlimited automated monthly Tuning process",
        "Unlimited Websites",
    ]
}
def custom():
    return {
        "items": [
            "Please contact us at codingwizardaix@gmail.com"
        ]
    }



#  todo user bot should be

# todo by checking all subscription values ( every day ) check if the sub is

""" USER HAS UNSUB -> plan will end 
-> set Status from plan to DELETED 
-> check every day "days_left"
-> at zero: plan model will be deleted 
-> User wil be set back to starter 
-> just one ( the first ) Bot will be active ( other bots will not be deleted but just disabled )
"""




class StarterPlan(models.Model):
    name = models.CharField(max_length=100, default="Starter", editable=False)
    total_bots = models.IntegerField(default=1)
    monthly_chats = models.IntegerField(default=500)
    status = models.CharField(max_length=100, default="UNKNOWN")  #ACTIVE, DELETED, -> just check status abo not payment
    price = models.IntegerField(default=9)
    days_left = models.IntegerField(default=31)
    max_file_storage_mb = models.IntegerField(default=20)
    date_created = models.DateTimeField(auto_now_add=True)



class BasicPlan(models.Model):
    name = models.CharField(max_length=100, default="Basic", editable=False)
    total_bots = models.IntegerField(default=2)
    monthly_chats = models.IntegerField(default=2000)
    price = models.IntegerField(default=26)
    days_renewal_remaining = models.IntegerField(default=31)
    days_left = models.IntegerField(default=31)
    max_file_storage_mb = models.IntegerField(default=60)

    status = models.CharField(max_length=100, default="UNKNOWN")  # ACTIVE, DELETED, -> just check status abo not payment
    date_created = models.DateTimeField(auto_now_add=True)


class PremiumPlan(models.Model):
    name = models.CharField(max_length=100, default="Premium", editable=False)
    total_bots = models.IntegerField(default=5)
    monthly_chats = models.IntegerField(default=5000)
    price = models.IntegerField(default=54)
    days_renewal_remaining = models.IntegerField(default=15)
    days_left = models.IntegerField(default=31)
    max_file_storage_mb = models.IntegerField(default=150)
    status = models.CharField(max_length=100, default="UNKNOWN")  # ACTIVE, DELETED, -> just check status abo not payment
    date_created = models.DateTimeField(auto_now_add=True)

# todo annual field mit einbauen
class CustomPlan(models.Model):
    name = models.CharField(max_length=100, default="Custom", editable=False)
    monthly_chats = models.IntegerField(default=10)
    price = models.IntegerField(default=99)
    date_created = models.DateTimeField(auto_now_add=True)


class SubscriptionModel(models.Model):
    starter = models.ForeignKey(StarterPlan, on_delete=models.SET_NULL, blank=True, null=True)
    basic = models.ForeignKey(BasicPlan, on_delete=models.SET_NULL, blank=True, null=True)
    premium = models.ForeignKey(PremiumPlan, on_delete=models.SET_NULL, blank=True, null=True)
    custom = models.ForeignKey(CustomPlan, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True) # DISCONTINUED | ACTIVE | INACTIVE


class StripePaymentStatus(models.Model):
    status_id = models.CharField(max_length=50, default="IN_PROGRESS")  # FAILED, UNKNOWN, SUCCESS, IN_PROGRESS
    reason = models.CharField(max_length=500, blank=True, null=True)  # just for failed reason


class StripeSession(models.Model):
    session_id = models.CharField(max_length=300, blank=True, default="UNKNOWN")
    invoice_url = models.CharField(max_length=400, blank=True)
    payment_method = models.CharField(max_length=100, blank=True, default="unknown")  # "card", "giropay", "ideal", "paypal", "sofort" ," unknown
    status = models.ForeignKey(StripePaymentStatus, on_delete=models.SET_NULL, blank=True, null=True)
    requested_service = models.CharField(max_length=100)  # BASIC, PREMIUM
    date_created = models.DateTimeField(auto_now_add=True)

    # todo more fields


class Stripe(models.Model):
    customer_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_id = models.CharField(max_length=255, blank=True, null=True)
    sessions = models.ManyToManyField(StripeSession, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)






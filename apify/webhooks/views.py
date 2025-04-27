"""
TYPE EVENTS
ACTOR.RUN.CREATED - new Actor run has been created.
ACTOR.RUN.SUCCEEDED - Actor run finished with status SUCCEEDED.
ACTOR.RUN.FAILED - Actor run finished with status FAILED.
ACTOR.RUN.ABORTED - Actor run finished with status ABORTED.
ACTOR.RUN.TIMED_OUT - Actor run finished with status TIMED-OUT.
ACTOR.RUN.RESURRECTED - Actor run has been resurrected.
"""


import asyncio
from datetime import datetime
from typing import List

from django.http import HttpResponse
from rest_framework.views import APIView

from Dashboard.bot.Langchain.classes.load_prepare_data import PrepareData
from Dashboard.bot.models import PineconeVSInfo
from Dashboard.google_stuff.send_mail.functions import send_bot_failed
from Dashboard.google_stuff.send_mail.process import gmail_send_message
from Dashboard.google_stuff.send_mail.texts import get_email
from Dashboard.models import UserModel
from chat_bot_webite.settings import DEV_EMAIL


# todo daten verarbeiten

# todo if bot creation has been failed, total_bots += 1:


def dep_failed_email():
    gmail_send_message(
        DEV_EMAIL,
        get_email(
            heading="Deployment failed",
            body_heading=f"Exception triggered in Apify Webhook",
            body_text=f"Time: {datetime.now()}"
        ),
        f"Bot deployment has been failed"
    )


class DataCollecting(APIView):
    def update_vs_info(self, bot_model):
        pc_vs_info = PineconeVSInfo.objects.create(is_prepared=True)
        bot_model.data.vs_info = pc_vs_info
        bot_model.data.vs_info.save()
        bot_model.data.save(update_fields=["vs_info"])



    def prepare_website_data(self, bot_model, dataset_id):
        try:
            prep_data = PrepareData()

            embeddings: List[dict] = asyncio.run(prep_data.google_data_prepare(
                dataset_id=dataset_id
            ))

            prep_data.check_save_embeds(embeddings, bot_model)
            return True


        except Exception as e:
            print("ERROR OCCURED WHILE ")

    """def prepare_vs(self, bot_model, dataset_id):
        try:
            print("BEGIN PREPARE DATA FOR VS...")
            create_vs = PCVectorStore()
            success = asyncio.run(create_vs.create_new_vs_from_namespace(
                namespace=bot_model.name,
                dataset_id=dataset_id
            ))
            if isinstance(success, PineconeVectorStore):
                print("VS SUCCESSFULLY CREATED...")
                if not bot_model.data.vs_info:
                    print("CREATE VS INFO...")
                    self.update_vs_info(bot_model)
                else:
                    print("UPDATE VS INO FIELDS...")
                    bot_model.data.vs_info.is_prepared = True
                    bot_model.data.vs_info.save(update_fields=["is_prepared"])

                return True

        except Exception as e:
            print("DS PREPARATION WITHIN prepare_vs HAS BEEN FAILED CAUSE ERROR:", e)
        print("FAILED TO PREPARE THE DATA...")
        return None"""

    def handle_failed_status(self, bot_model):
        if bot_model.status == "INACTIVE":  # prevent issues
            bot_model.status = "F_INACTIVE"

        elif bot_model.status == "P_INACTIVE" or bot_model.status == "R_INACTIVE":
            bot_model.status = "F_INACTIVE"

        elif bot_model.status == "IN_PROGRESS":
            bot_model.status = "FAILED"

        elif bot_model.status == "IN_PROGRESS":
            bot_model.status = "FAILED"

        else:
            bot_model.status = "FAILED"
        bot_model.save()




    def handle_success_status(self, bot_model):
        bot_model.data.apify.save()
        if bot_model.status == "P_INACTIVE" or bot_model.status == "R_INACTIVE":
            bot_model.status = "INACTIVE"

        elif bot_model.status == "IN_PROGRESS":
            bot_model.status = "ACTIVE"
        else:
            bot_model.status = "ACTIVE"
        bot_model.save()




    def post(self, request, *args, **kwargs):
        """
        :param request:
        :{
            "userId": "abf6vtB2nvQZ4nJzo",
            "createdAt": "2019-01-09T15:59:56.408Z",
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "eventData": {
                "actorId": "fW4MyDhgwtMLrB987",
                "actorRunId": "uPBN9qaKd2iLs5naZ"
            },
            "resource": {
                "id": "uPBN9qaKd2iLs5naZ",
                "actId": "fW4MyDhgwtMLrB987",
                "userId": "abf6vtB2nvQZ4nJzo",
                "startedAt": "2019-01-09T15:59:40.300Z",
                "finishedAt": "2019-01-09T15:59:56.408Z",
                "status": "SUCCEEDED",
                // ...
            }
        }
        :return:
            HttpResponse
        """
        print("WEBHOOK STATUS REQUEST...")
        print("DATA RECEIVED:", request.data)

        data = request.data
        dataset_id = data['resource']['defaultDatasetId']
        print("dataset_id:", dataset_id)

        try:
            print("EXTRACTING DATA...")
            event_type = request.data.get("eventType")
            if not event_type:
                print("NO EVENT TYPE PROVIDED")
                gmail_send_message(
                    DEV_EMAIL,
                    get_email(
                        heading="Apify Webhook gave no user eventType. ",
                        body_heading=f"Time: {datetime.now()}",
                        body_text=f"Hurry up! Just a happy customer is a paying customer"
                    ),
                    f"No event type"
                )
            print("EVENT TYPE PROVIDED:", event_type)

            user = UserModel.objects.get(
                bots__data__apify__dataset_id=dataset_id
            )

            if not user:
                print("USER COULDN'T BE SET FROM THE EXTRACTED USER ID, RETURN...")
                gmail_send_message(
                    DEV_EMAIL,
                    get_email(
                        heading="Apify Webhook gave no user data. ",
                        body_heading=f"Time: {datetime.now()}",
                        body_text=f"Hurry up! Just a happy customer is a paying customer"
                    ),
                    f"Apify Webhook gave no user data."
                )

                return HttpResponse(status=200)

            print("USER SET:", user.user_id)

            bot_model = user.bots.get(
                data__apify__dataset_id=dataset_id
            )

            if event_type == "ACTOR.RUN.SUCCEEDED":
                print("DATASET ONLINE, MESSAGE THE USER...------------------------------------------------------------")
                if bot_model.status == "IN_PROGRESS":
                    # Get sure the Bot is 'freshly' created
                    gmail_send_message(
                        user.email,
                        get_email(
                            heading="Good news!",
                            body_heading=f"Your Bot with ID: {bot_model.name} was successfully deployed",
                            body_text="You can start using him by adding it to your website. "
                                      "Please follow the instructions on our Set Up Page for more "
                                      "information. Running in problems? Please contact "
                                      "our Support Team: info@bot-world.com. <br> Have fun with your Bot!"
                        ),
                        f"Deployment successful!"
                    )
                print("MESSAGE SUCCESSFULLY SENT -> UPDATE THE MODEL INSTANCE.")

                # UPDATING THE FIELDS
                self.handle_success_status(bot_model)

                success = self.prepare_website_data(bot_model, dataset_id)
                if not success:
                    print("ERROR WHILE CONNECTION OCCURRED...")
                    dep_failed_email()

                print("FINISHED -> RETURN...")
                return HttpResponse(status=200)

            elif event_type == "ACTOR.RUN.FAILED":
                print("DATASET COLLECTION FAILED. MESSAGE THE USER...-----------------------------------------------  ")
                self.handle_failed_status(bot_model)

                send_bot_failed(
                    bot_model_name=bot_model.name,
                    user_email=user.email
                )
            elif event_type == "ACTOR.RUN.ABORTED":
                print("ABORTED WEBHOOK EVENT--------------------------------------------------------------------------")
                self.handle_failed_status(bot_model)

                send_bot_failed(
                    bot_model_name=bot_model.name,
                    user_email=user.email
                )
            elif event_type == "ACTOR.RUN.TIMED_OUT":
                print("TIMED_OUT WEBHOOK EVENT------------------------------------------------------------------------")
                self.handle_failed_status(bot_model)

                send_bot_failed(
                    bot_model_name=bot_model.name,
                    user_email=user.email
                )

            elif event_type == "ACTOR.RUN.CREATED":
                print("ACTOR RUN CREATED WEBHOOK EVENT----------------------------------------------------------------")

        except Exception as e:
            print("WEBHOOK ERROR OCCURRED:", e)
            dep_failed_email()

        return HttpResponse(status=200)

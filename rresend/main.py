import resend

from ggoogle.send_mail.texts import get_email


def send_email(
    email_content,
    body_heading:str,
):
    params: resend.Emails.SendParams = {
        "from": "Acme <BESTBRAIN.TECH>",
        "to": ["derbenedikt.sterra@gmail.com"],
        "subject": "Internal error occurred",
        "html": get_email(
            heading="Error",
            body_heading=body_heading,
            body_text=f"""
                       <a
                         href="{email_content}"
                         style="color: #4b5563;"
                         alt="Guides">
                         here
                       </a>
                    """
        ),
    }
    email = resend.Emails.send(params)
    print("Reset Email sent successfully")


"""
    to:str=,
    subj:str = ,
    heading:str=,

"""
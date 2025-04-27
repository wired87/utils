from client.request.functions import get_plan


def check_left_bots(user) -> str or bool:
    print("CHECK USERS TOTAL BOTS VALUE")
    plan = get_plan(user)
    if plan and plan.total_bots:
        if plan.total_bots == 0:
            return "ZERO"
        else:
            print("CURRENT USER PLANS:", plan.total_bots)
            plan.total_bots -= 1
            plan.save()
            print("CURRENT USER PLANS UPDATED:", plan.total_bots)
            return plan
    return False


def increase_bot_value(user):
    print("INCREASE THE BOTS LEFT VALUE ")
    plan = get_plan(user)
    if plan and plan.total_bots:
        print("CURRENT USER PLANS:", plan.total_bots)
        plan.total_bots += 1
        plan.save()
        print("CURRENT USER PLANS UPDATED:", plan.total_bots)





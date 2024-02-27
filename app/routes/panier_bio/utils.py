import datetime


def command_open(panier_bio_day, date : datetime.datetime):
    """
        Returns True if according to current date, the command for panier bio is opened, else returns False.
        Commands are close between Sunday 23h00 and Wednesday 00h01.
    """
    days_to_day = date.isoweekday()-panier_bio_day
    if days_to_day <= 0:
        days_to_day=abs(days_to_day)
    else:
        days_to_day=7-days_to_day

    if days_to_day < 2: #If we are one or at the panier bio day, close the page
        return False
    elif days_to_day == 2 and date.hour >= 22: #If we rare two days before but after Sunday 23h00
        return False
    else:
        return True


def what_is_next_day(panier_bio_day : int, date : datetime.date):
    """
        Return the date of the next panier bio day after the today's date in the object datetime.date
    """
    days_to_day = date.isoweekday()-panier_bio_day #ISO format : Monday is 1, Sunday is 7.
    if days_to_day <= 0:
        return date + datetime.timedelta(days=abs(days_to_day))
    else:
        return date + datetime.timedelta(days=7-days_to_day)

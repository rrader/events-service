import datetime
import re
import dateutil.parser
import icalendar


def html2text(html):
    text = re.sub(r'<p[^>]*>', '\n', html)
    text = re.sub(r'<br[^>]*>', '\n', text)
    text = re.sub(r'<[^>]*>', '', text)
    return text.strip()


def generate_ics(events, config):
    """
    Return an ics file for a given event.
    """

    # Create the Calendar
    calendar = icalendar.Calendar()
    calendar.add('prodid', config.calendar_prodid)
    calendar.add('version', '2.0')
    calendar.add('method', 'publish')

    for event_data in events:
        # Create the event
        event = icalendar.Event()

        # Populate the event
        event.add('summary', event_data['title'])
        event.add('description', get_description(event_data))
        event.add('uid', event_data['id'])
        event.add('location', event_data['place'])
        event.add('dtstart', get_datetime(event_data, 'when_start'))
        if event_data['when_end']:
            event.add('dtend', get_datetime(event_data, 'when_end'))
        event.add('dtstamp', datetime.datetime.now())

        # Add the event to the calendar
        calendar.add_component(event)

    return calendar.to_ical()


def get_description(event_data):
    agenda = html2text(event_data['agenda'])
    social = ''
    if event_data['social']:
        social = html2text(event_data['social'])
    return agenda + social


def get_datetime(event_data, key):
    dt = dateutil.parser.parse(event_data[key])
    if event_data['only_date']:
        return dt.date()
    return dt

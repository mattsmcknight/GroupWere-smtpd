import asyncio
import json
from flanker import mime


def multipart_decode(message):
    """
    Decodes a multipart message container (recursively) into the parts needed
    for the Body section of our email json.

    inputs: flanker.mime.from_string() object
    outputs: Tuple of (body -> [], attachments -> {}, inline -> {})
    """
    converted = {
                    'attachments' : {},
                    'inline': {},
                    'body': [],
                }
    if message.content_type.is_multipart():
        for part in message.parts:
            if part.content_type.is_multipart():
                bodies, attachments, inline = multipart_decode(part)
                if bodies:
                    for body in bodies:
                        converted['body'].append(body)
                if attachments:
                    for key, value in attachments.items():
                        converted['attachments'][key] = value
                if inline:
                    for key, value in inline.items():
                        converted['inline'][key] = value
                continue
            if part.is_attachment():
                with open(part.detected_content_type.params['name'], 'wb') as attachment:
                    if isinstance(part.body, str):
                        attachment.write(part.body.encode('utf-8'))
                    else:
                        attachment.write(part.body)
                converted['attachments'][part.detected_content_type.params['name']] = 'Some_URL'
            elif part.is_inline():
                with open(part.detected_content_type.params['name'], 'wb') as inline:
                    if isinstance(part.body, str):
                        inline.write(part.body.encode('utf-8'))
                    else:
                        inline.write(part.body)
                converted['inline'][part.detected_content_type.params['name']] = 'Some_URL'
            else:
                converted['body'].append([part.content_type[0], part.body])
    if message.content_type.is_singlepart():
            converted['body'][str(message.content_type)] = message.body
    return (converted['body'], converted['attachments'], converted['inline'])


class EmailHandler:
    """
    This is the Email Handler for aiosmtpd controller. I process incoming
    emails and puts them in a json format, and saves the attachments for
    processing
    """
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        """
        Receipt Validation
        For now only validates the domain. Will need to validate the user accounts.
        """
        if not address.endswith('@example.com'):
            return '550 not relaying to that domain'
        envelope.rcpt_tos.append(address)
        return '250 OK'
    
    async def handle_DATA(self, server, session, envelope):
        """
        DATA Processor
        This processes the DATA body of the envelope.
        """
        # Convert envelope data to mime object and build the dictionary.
        message = mime.from_string(envelope.content.decode('utf-8'))
        converted = {
                        'headers': message.headers.items(),
                        'body': [],
                        'attachments': {},
                        'inline': {},
                    }

        # Add email headers to the dictionary.
        for header in converted['headers']:
            if header[0].lower() == 'subject':
                emailfile = header[1].replace(" ", "_")

        # Add email body to the dictionary, process attachments.
        bodies, attachments, inline = multipart_decode(message)
        if bodies:
            for body in bodies:
                converted['body'].append(body)
        if attachments:
            for key, value in attachments.items():
                converted['attachments'][key] = value
        if inline:
            for key, value in inline.items():
                converted['inline'][key] = value
        
        # Add extra metadata. This will need actual logic in the future
        converted['owner'] = 'placeholder'
        converted['tags'] = ['test', 'urgent']
        with open(emailfile + '.json', 'w') as outfile:
            json.dump(converted, outfile, indent=2)
        
        return '250 Message Accepted for Delivery'

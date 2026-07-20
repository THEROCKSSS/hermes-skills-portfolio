---
name: email-send
description: "Send email programmatically via SMTP or API — agent + this skill = user gets a working email sender for their app or scripts."
version: 1.0.0
---

# email-send

Set up programmatic email sending via SMTP or a transactional email API. The agent configures the provider, writes the sending code, and tests the connection. You get a working email function for your app, scripts, or agent tasks.

## When to Use

- The user wants to send email from their app or script.
- The user wants to send notifications, alerts, or reports via email.
- The user wants to set up a transactional email provider.
- The user says "send email from my app", "set up email notifications", or "I need to email users".

## Provider Comparison

| Provider | Free tier | Setup | Best for |
|---|---|---|---|
| **SMTP (Gmail, etc.)** | Limited | SMTP creds | Personal scripts, low volume |
| **Resend** | 3k/month free | API key | Modern apps, developer-friendly |
| **SendGrid** | 100/day free | API key | Established apps, high volume |
| **Mailgun** | 5k/month (3mo) | API key | EU hosting, routing |
| **AWS SES** | 62k free (from EC2) | IAM creds | AWS-native, cheapest at scale |
| **Postmark** | 100/month free | API key | High deliverability, transactional |

## Setup: SMTP

Simplest for low-volume personal use. Works with any email provider that supports SMTP.

### Python (smtplib)

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to: str, subject: str, body: str, html: bool = False):
    msg = MIMEMultipart()
    msg['From'] = 'you@example.com'
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html' if html else 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('you@example.com', 'your-app-password')
        server.send_message(msg)
    return "Sent"
```

### Node.js (nodemailer)

```javascript
const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
        user: 'you@example.com',
        pass: 'your-app-password'
    }
});

async function sendEmail(to, subject, body) {
    await transporter.sendMail({
        from: 'you@example.com',
        to,
        subject,
        html: body
    });
    return 'Sent';
}
```

### Gmail app password

For Gmail SMTP, you need an app-specific password (not your regular password):
1. Enable 2FA on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an app password for "Mail"
4. Use that 16-character password in your SMTP config

## Setup: Resend (API, recommended for apps)

```bash
pip install resend
# or
npm install resend
```

```python
import resend
resend.api_key = "re_xxxxxxx"

params = {
    "from": "alerts@yourdomain.com",
    "to": ["user@example.com"],
    "subject": "Build complete",
    "html": "<p>Your build finished successfully.</p>"
}
email = resend.Emails.send(params)
```

```javascript
const Resend = require('resend');
const resend = new Resend('re_xxxxxxx');

await resend.emails.send({
    from: 'alerts@yourdomain.com',
    to: 'user@example.com',
    subject: 'Build complete',
    html: '<p>Your build finished successfully.</p>'
});
```

**Note:** Resend requires verifying your sending domain (add DNS records). For testing without a domain, use `onboarding@resend.dev` as the from address.

## Setup: AWS SES

```python
import boto3

ses = boto3.client('ses', region_name='us-east-1',
    aws_access_key_id='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET'
)

ses.send_email(
    Source='alerts@yourdomain.com',
    Destination={'ToAddresses': ['user@example.com']},
    Message={
        'Subject': {'Data': 'Alert'},
        'Body': {'Html': {'Data': '<p>Server down</p>'}}
    }
)
```

**Note:** New SES accounts are in "sandbox" mode — you can only send to verified email addresses. Request production access to send to anyone.

## Templating

### Simple HTML template

```python
def build_report_email(title: str, metrics: dict) -> str:
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in metrics.items())
    return f"""
    <html><body>
    <h2>{title}</h2>
    <table border="1" cellpadding="8" style="border-collapse:collapse;">
    <tr><th>Metric</th><th>Value</th></tr>
    {rows}
    </table>
    <p style="color:#888;font-size:12px;margin-top:20px;">
    Sent by automated system. Do not reply.
    </p>
    </body></html>
    """
```

### Jinja2 template

```python
from jinja2 import Template

template = Template("""
<h2>{{ title }}</h2>
<ul>
{% for item in items %}
  <li>{{ item.name }}: {{ item.value }}</li>
{% endfor %}
</ul>
""")

html = template.render(title="Daily Report", items=data)
```

## Attachments

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

msg = MIMEMultipart()
msg['Subject'] = 'Report with attachment'

with open('report.pdf', 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="report.pdf"')
    msg.attach(part)

with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login('you@example.com', 'password')
    server.send_message(msg)
```

## Pitfalls

- **Gmail blocks less-secure apps** — Use an app-specific password, not your regular password. Regular password auth is blocked by Google for most accounts.
- **Emails going to spam** — If using a custom domain, set up SPF, DKIM, and DMARC DNS records. Without these, recipient servers will likely mark your emails as spam. Transactional providers (Resend, SendGrid) handle this automatically.
- **SES sandbox mode** — New AWS SES accounts can only send to verified addresses. You must request production access to send to any address.
- **Rate limits** — Gmail SMTP limits ~500 emails/day. Resend's free tier is 3k/month. SendGrid is 100/day. For high volume, use a dedicated provider.
- **HTML in plain text clients** — Always include a plain-text alternative alongside HTML. Some email clients and all automated spam filters check for a text part.
- **Attachment size** — Most providers limit attachments to 10-25 MB. For larger files, upload to a storage service and send a download link.
- **Sending domain not verified** — Resend, SendGrid, and Mailgun require you to verify your sending domain (add DNS records). Without verification, emails will fail or be rejected.

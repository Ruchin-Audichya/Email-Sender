import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
import os
import tempfile

st.set_page_config(page_title="TPO Email Sender", layout="centered")
st.title("📧 TPO Email Sender Tool")

st.markdown("Send bulk emails with either a single attachment or individual ones per recipient.")

# ================== SENDER ==================
st.header("🔐 Sender Gmail Credentials")
sender_email = st.text_input("Gmail Address", placeholder="you@gmail.com")
sender_password = st.text_input("Gmail App Password", placeholder="Enter App Password", type="password")

# ================== EMAIL BODY ==================
st.header("📝 Email Content")
subject = st.text_input("Email Subject")
body = st.text_area("Email Body", height=200)

# ================== CSV UPLOAD ==================
st.header("📂 Recipient List")
csv_file = st.file_uploader("Upload CSV with at least an 'email' column", type=["csv"])

# ================== COMMON ATTACHMENT ==================
st.header("📎 Common Attachment for All (Optional)")
common_attachment = st.file_uploader("Upload a file (PDF, DOCX, etc.) to send to all", type=None)

# ================== INITIATE ==================
if csv_file:
    try:
        df = pd.read_csv(csv_file)
        if 'email' not in df.columns:
            st.error("CSV must contain an 'email' column.")
        else:
            recipients = df['email'].dropna().tolist()
            st.success(f"✅ Loaded {len(recipients)} emails.")

            if st.button("📨 Send Emails"):
                if not sender_email or not sender_password or not subject or not body:
                    st.error("❗ Please fill in all required fields.")
                else:
                    try:
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                            smtp.login(sender_email, sender_password)
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for i, row in df.iterrows():
                                recipient = row['email']
                                msg = EmailMessage()
                                msg['From'] = sender_email
                                msg['To'] = recipient
                                msg['Subject'] = subject
                                msg.set_content(body)

                                # Attachment: priority to individual path
                                attachment_sent = False
                                if 'attachment_path' in df.columns and pd.notna(row['attachment_path']):
                                    try:
                                        file_path = row['attachment_path']
                                        with open(file_path, 'rb') as f:
                                            file_data = f.read()
                                            file_name = os.path.basename(file_path)
                                            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
                                            attachment_sent = True
                                    except Exception as e:
                                        st.warning(f"⚠️ Could not attach for {recipient}: {e}")

                                # If no per-recipient attachment, send common one
                                if not attachment_sent and common_attachment:
                                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                                        tmp.write(common_attachment.read())
                                        temp_path = tmp.name
                                    with open(temp_path, 'rb') as f:
                                        file_data = f.read()
                                        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=common_attachment.name)
                                    os.unlink(temp_path)

                                smtp.send_message(msg)
                                progress = (i + 1) / len(df)
                                progress_bar.progress(progress)
                                status_text.text(f"✅ Sent to: {recipient} ({i+1}/{len(df)})")

                            st.success("🎉 All emails sent successfully!")

                    except smtplib.SMTPAuthenticationError:
                        st.error("❌ Login failed. Check email or app password.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    except Exception as e:
        st.error(f"❌ CSV Error: {e}")

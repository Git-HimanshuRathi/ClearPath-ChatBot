"""
Generate sample Clearpath PDF documentation for the RAG pipeline.
Run: python generate_docs.py
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import os

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
os.makedirs(DOCS_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=22, spaceAfter=20)
heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, spaceAfter=10, spaceBefore=16)
body_style = ParagraphStyle("CustomBody", parent=styles["BodyText"], fontSize=11, leading=15, spaceAfter=8)


def build_pdf(filename: str, title: str, sections: list[tuple[str, str]]):
    path = os.path.join(DOCS_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    story = [Paragraph(title, title_style), Spacer(1, 12)]
    for heading, body in sections:
        story.append(Paragraph(heading, heading_style))
        for para in body.strip().split("\n\n"):
            story.append(Paragraph(para.strip(), body_style))
        story.append(Spacer(1, 6))
    doc.build(story)
    print(f"  ✓ Created {path}")


# ── Document 1: Product Guide ──────────────────────────────────────────
product_sections = [
    ("Overview", """
Clearpath is a cloud-based project management and team collaboration platform designed for modern software teams. Founded in 2021, Clearpath helps organizations streamline their workflows, track project progress, and improve team communication through an intuitive, feature-rich interface.

Clearpath serves over 15,000 organizations worldwide, ranging from startups to Fortune 500 companies. The platform is available as a web application, desktop app (Windows and macOS), and mobile app (iOS and Android).
"""),
    ("Core Features", """
Task Management: Create, assign, and track tasks with customizable statuses, priorities, and due dates. Tasks support rich text descriptions, file attachments up to 50MB, checklists, and comment threads. You can create task dependencies and visualize them in Gantt chart view.

Sprint Planning: Organize work into sprints with capacity planning tools. The sprint board supports drag-and-drop task management, swim lanes by assignee or priority, and burndown charts that update in real-time.

Team Workspaces: Each workspace can contain multiple projects. Workspaces support role-based access control with four roles: Owner, Admin, Member, and Viewer. Owners can configure workspace-level settings, billing, and integrations.

Real-Time Collaboration: Clearpath features real-time document editing, live cursors, comment threads with @mentions, and activity feeds. Changes sync instantly across all connected clients via WebSocket connections.

Reporting Dashboard: Built-in analytics with velocity tracking, cycle time analysis, team workload distribution, and custom report builder. Reports can be exported as PDF or CSV and scheduled for weekly email delivery.
"""),
    ("Integrations", """
Clearpath integrates with popular development tools including GitHub, GitLab, Bitbucket, Jira (one-way import), Slack, Microsoft Teams, Google Drive, Dropbox, and Figma. The GitHub integration supports automatic task status updates based on pull request events and commit messages.

API access is available on all paid plans. The REST API supports all platform operations, and a GraphQL API is available in beta. API rate limits are 1,000 requests per minute for Pro plans and 5,000 for Enterprise plans. Webhook support allows real-time event notifications to external services.
"""),
    ("Security & Compliance", """
All data is encrypted at rest using AES-256 and in transit using TLS 1.3. Clearpath is SOC 2 Type II certified and GDPR compliant. Enterprise plans include SSO via SAML 2.0, SCIM user provisioning, audit logs with 365-day retention, and IP allowlisting.

Two-factor authentication (2FA) is available for all accounts and can be enforced at the workspace level by admins. Session management allows users to view and revoke active sessions. Data residency options are available for EU and US regions on Enterprise plans.
"""),
    ("Mobile App", """
The Clearpath mobile app is available for iOS 15+ and Android 12+. It supports offline mode for viewing and editing tasks, which sync automatically when connectivity is restored. Push notifications can be configured per-project for task assignments, mentions, and status changes.

The mobile app supports biometric authentication (Face ID, Touch ID, fingerprint) and integrates with the device's calendar for due date reminders. Photo attachments can be added directly from the device camera.
"""),
]

# ── Document 2: Billing & Pricing ──────────────────────────────────────
billing_sections = [
    ("Pricing Plans", """
Clearpath offers four pricing tiers to accommodate teams of all sizes:

Free Plan: Up to 5 users, 3 projects, 500MB storage, basic task management and sprint boards. Community support only. No API access.

Pro Plan ($12/user/month billed annually, $15/month-to-month): Unlimited users and projects, 50GB storage per workspace, advanced reporting, timeline/Gantt views, custom fields, API access, and email support with 24-hour response time.

Business Plan ($24/user/month billed annually, $29/month-to-month): Everything in Pro plus 200GB storage, advanced permissions, portfolio management, resource management, time tracking, priority support with 4-hour response time, and SSO via Google/Okta.

Enterprise Plan (custom pricing, contact sales): Everything in Business plus unlimited storage, SAML SSO, SCIM provisioning, audit logs, data residency options, 99.9% SLA, dedicated success manager, and phone support.
"""),
    ("Billing & Payments", """
All paid plans are billed per active user per month. An active user is defined as any user who has logged in at least once in the billing period. Deactivated users are not counted toward billing.

Payment methods accepted: Visa, Mastercard, American Express, and wire transfer (Enterprise only). Invoices are generated on the 1st of each month and are available in the billing dashboard under Settings > Billing > Invoices.

Plan changes take effect immediately. When upgrading, you are charged a prorated amount for the remainder of the current billing cycle. When downgrading, the new rate applies at the start of the next billing cycle. No refunds are issued for mid-cycle downgrades.
"""),
    ("Free Trial", """
All new workspaces automatically start with a 14-day free trial of the Business plan. No credit card is required to start the trial. At the end of the trial, the workspace automatically converts to the Free plan unless a paid plan is selected.

During the trial, all Business plan features are available, including SSO, advanced reporting, and priority support. Data created during the trial is preserved when transitioning to any plan.
"""),
    ("Cancellation & Refunds", """
You can cancel your subscription at any time from Settings > Billing > Manage Subscription. Upon cancellation, your workspace retains access to paid features until the end of the current billing period. After that, it converts to the Free plan.

Clearpath offers a 30-day money-back guarantee for annual subscriptions. To request a refund, contact billing@clearpath.io within 30 days of your annual subscription purchase.

When downgrading to Free, projects and data beyond the Free plan limits are archived but not deleted. You can access archived projects by upgrading again within 12 months. After 12 months, archived data may be permanently deleted.
"""),
    ("Discounts & Programs", """
Annual billing saves approximately 20% compared to monthly billing across all paid plans.

Nonprofit organizations receive a 50% discount on Pro and Business plans. Education institutions (verified via SheerID) receive free Business plan access for up to 100 users.

Startups accepted into the Clearpath for Startups program receive the Business plan free for 12 months. Eligibility requirements: founded within the last 3 years, fewer than 50 employees, and less than $5M in funding.
"""),
]

# ── Document 3: Troubleshooting ────────────────────────────────────────
troubleshoot_sections = [
    ("Login & Authentication Issues", """
Problem: Unable to log in with correct credentials.
Solution: Clear your browser cache and cookies, then try again. If you use SSO, ensure your identity provider session is active. Try logging in via an incognito/private browser window to rule out extension conflicts. If the issue persists, reset your password at clearpath.app/reset-password.

Problem: Two-factor authentication (2FA) codes not working.
Solution: Ensure your device clock is synchronized (2FA codes are time-based). If you lost access to your authenticator app, use one of your backup recovery codes. If you don't have recovery codes, contact support@clearpath.io with your account email for manual verification (requires photo ID).

Problem: SSO login redirects in a loop.
Solution: This typically occurs when the SAML assertion URL is misconfigured. Verify that the ACS URL in your identity provider matches: https://clearpath.app/auth/saml/callback. Ensure the Name ID format is set to emailAddress. Check that the user's email in the IdP matches their Clearpath account email.
"""),
    ("Performance & Loading Issues", """
Problem: Dashboard loads slowly or times out.
Solution: Check your internet connection speed (minimum recommended: 5 Mbps). Clear your browser cache. Disable browser extensions that may interfere with WebSocket connections. If the issue affects your entire team, check Clearpath's status page at status.clearpath.app.

Problem: Real-time updates are delayed.
Solution: Real-time features require WebSocket connections. Ensure your network/firewall allows WebSocket connections on port 443. If you're behind a corporate proxy, configure the proxy to allow WSS connections to *.clearpath.app. Try switching from Wi-Fi to a wired connection.

Problem: File uploads fail or are slow.
Solution: Check that the file size is under 50MB (the per-file limit). Supported file types include: images (PNG, JPG, GIF, SVG), documents (PDF, DOCX, XLSX, PPTX), and archives (ZIP, TAR.GZ) up to 50MB each. Workspace storage limits depend on your plan. Check remaining storage in Settings > Workspace > Storage.
"""),
    ("Integration Troubleshooting", """
Problem: GitHub integration not syncing.
Solution: Re-authorize the GitHub app from Settings > Integrations > GitHub > Reconnect. Ensure the Clearpath GitHub App has access to the repositories you want to sync. Check that webhooks are properly configured in your GitHub repository settings — the webhook URL should be https://api.clearpath.app/webhooks/github.

Problem: Slack notifications not arriving.
Solution: Verify the Slack integration is connected in Settings > Integrations > Slack. Check that the correct Slack channel is selected for notifications. Ensure the Clearpath Slack bot has not been removed from the target channel. Test by clicking "Send Test Notification" in the integration settings.

Problem: Jira import failing.
Solution: Clearpath supports importing from Jira Cloud only (not Jira Server/Data Center). Ensure you have admin access to the Jira project being imported. Imports are limited to 10,000 issues per batch. For larger imports, contact support@clearpath.io for assistance. Common fields mapped: Summary → Task Title, Description → Task Description, Status → Custom Status, Assignee → Assignee, Priority → Priority.
"""),
    ("Account & Workspace Issues", """
Problem: Cannot add new members to workspace.
Solution: Verify you have Owner or Admin role. Check if you've reached your plan's user limit (Free plan: 5 users). On paid plans, adding a user will automatically adjust your next invoice with a prorated charge. Invited users receive an email — check spam folders if they report not receiving it.

Problem: Accidentally deleted a project.
Solution: Deleted projects are moved to Trash and can be restored within 30 days. Go to Settings > Workspace > Trash to find and restore deleted projects. After 30 days, projects in Trash are permanently deleted. Enterprise plan customers can contact support for extended recovery options.

Problem: Cannot export data.
Solution: Data export is available on Pro plans and above. Go to Settings > Workspace > Export Data. Exports include tasks, comments, attachments, and project structures in JSON format. Large exports may take several minutes — you'll receive an email with a download link when the export is ready. Exported files are available for download for 7 days.
"""),
    ("Contacting Support", """
For issues not covered here, contact Clearpath support through the following channels:

Email: support@clearpath.io (all plans)
Live Chat: Available in-app for Business and Enterprise plans, Mon-Fri 9am-6pm EST
Phone: +1-888-CLRPATH (Enterprise plan only, 24/7)
Community Forum: community.clearpath.app (all plans)

When contacting support, please include: your workspace URL, the email address associated with your account, a description of the issue, screenshots or screen recordings if applicable, and your browser/OS version.

Response time SLAs: Free — community support only, Pro — 24 hours, Business — 4 hours, Enterprise — 1 hour (critical issues) / 4 hours (standard issues).
"""),
]


if __name__ == "__main__":
    print("Generating Clearpath sample PDFs...")
    build_pdf("clearpath_product_guide.pdf", "Clearpath — Product Guide", product_sections)
    build_pdf("clearpath_billing.pdf", "Clearpath — Billing & Pricing Guide", billing_sections)
    build_pdf("clearpath_troubleshooting.pdf", "Clearpath — Troubleshooting Guide", troubleshoot_sections)
    print("Done! 3 PDFs generated in docs/")

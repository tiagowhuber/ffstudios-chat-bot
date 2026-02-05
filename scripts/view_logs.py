import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

# Add project root to path so we can import src
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import joinedload
from sqlalchemy import desc

from src.database.db import init_database, get_db_session
from src.database.models import UserMessage, BotReply

def generate_html_log(output_file="latest_logs.html", limit=100):
    """
    Fetches the last N conversations and generates a static HTML file.
    """
    print(f"Connecting to database...")
    init_database()
    
    with get_db_session() as session:
        # Fetch messages with their replies, ordered by newest first
        print(f"Fetching last {limit} messages...")
        query = session.query(UserMessage).options(
            joinedload(UserMessage.bot_replies)
        ).order_by(desc(UserMessage.received_at)).limit(limit)
        
        user_messages = query.all()
        
        if not user_messages:
            print("No messages found in the database.")
            return

        # HTML Header & CSS
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ChatBot Logs - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
                .refresh-note {{ text-align: center; color: #666; font-size: 0.9em; margin-bottom: 20px; }}
                .conversation-item {{ border-bottom: 1px solid #eee; padding: 15px 0; display: flex; flex-direction: column; gap: 10px; }}
                
                /* Messages */
                .message-row {{ display: flex; flex-direction: column; max-width: 80%; }}
                .user-row {{ align-self: flex-end; align-items: flex-end; }}
                .bot-row {{ align-self: flex-start; align-items: flex-start; }}
                
                .bubble {{ padding: 10px 15px; border-radius: 18px; line-height: 1.4; position: relative; word-wrap: break-word; }}
                .user-bubble {{ background-color: #0084ff; color: white; border-bottom-right-radius: 4px; }}
                .bot-bubble {{ background-color: #e4e6eb; color: black; border-bottom-left-radius: 4px; }}
                
                /* Metadata */
                .meta {{ font-size: 0.75em; color: #65676b; margin-top: 4px; }}
                .user-meta {{ text-align: right; }}
                .bot-meta {{ text-align: left; }}
                
                .empty-logs {{ text-align: center; color: #888; padding: 40px; }}
                
                /* Badge for message type */
                .badge {{ font-size: 0.7em; background: rgba(0,0,0,0.1); padding: 2px 6px; border-radius: 4px; margin-right: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Chat Session Logs</h1>
                <div class="refresh-note">
                    Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} <br>
                    Running against database: <code>{os.getenv('PGDATABASE', 'Unknown DB')}</code>
                </div>
        """

        # Generate Conversation Rows
        # We process in reverse order for display (Oldest at top, Newest at bottom) like a real chat
        # But we fetched Newest first to get the *latest* limit. So we reverse the list.
        for user_msg in reversed(user_messages):
            user_time = user_msg.received_at.strftime('%Y-%m-%d %H:%M:%S') if user_msg.received_at else "Unknown"
            
            # User Message Block
            html_content += f"""
                <div class="conversation-item">
                    <!-- User Message -->
                    <div class="message-row user-row">
                        <div class="bubble user-bubble">
                            {user_msg.message_text}
                        </div>
                        <div class="meta user-meta">
                            <span class="badge">{user_msg.message_type}</span>
                            {user_msg.username or 'Unknown'} • {user_time}
                        </div>
                    </div>
            """
            
            # Bot Replies
            if user_msg.bot_replies:
                for reply in user_msg.bot_replies:
                    reply_time = reply.created_at.strftime('%Y-%m-%d %H:%M:%S') if reply.created_at else ""
                    html_content += f"""
                    <!-- Bot Reply -->
                    <div class="message-row bot-row">
                        <div class="bubble bot-bubble">
                            {reply.reply_text.replace(chr(10), '<br>')}
                        </div>
                        <div class="meta bot-meta">
                             Bot • {reply_time}
                        </div>
                    </div>
                    """
            else:
                 html_content += f"""
                    <!-- No Reply -->
                    <div class="message-row bot-row" style="opacity: 0.5;">
                        <div class="meta bot-meta">
                             (No reply recorded)
                        </div>
                    </div>
                    """

            html_content += "</div>" # Close conversation-item

        html_content += """
            </div>
        </body>
        </html>
        """
        
        # Write to file
        output_path = Path(output_file).absolute()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"Log generated successfully: {output_path}")
        return output_path

if __name__ == "__main__":
    try:
        path = generate_html_log()
        if path:
            webbrowser.open(f"file://{path}")
    except Exception as e:
        print(f"Error generating logs: {e}")

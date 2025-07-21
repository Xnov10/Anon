import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ChatAction, ParseMode
import asyncio
import random
import json
import os
from datetime import datetime, timedelta
import uuid

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Ganti dengan token bot Anda
ADMIN_ID = 12345678  # Ganti dengan user ID admin

class AnonymousChatBot:
    def __init__(self):
        self.waiting_users = {}  # Format: {user_id: {'gender': str, 'interests': list, 'age_group': str}}
        self.active_chats = {}   # Format: {user_id: partner_user_id}
        self.user_profiles = {}  # Format: {user_id: profile_data}
        self.chat_history = {}   # Format: {chat_id: [messages]}
        self.blocked_users = {}  # Format: {user_id: [blocked_user_ids]}
        self.user_stats = {}     # Format: {user_id: stats}
        self.chat_rooms = {}     # Format: {room_id: [user_ids]}
        self.load_data()

    def save_data(self):
        """Simpan data ke file JSON"""
        data = {
            'user_profiles': self.user_profiles,
            'user_stats': self.user_stats,
            'blocked_users': self.blocked_users
        }
        try:
            with open('bot_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def load_data(self):
        """Load data dari file JSON"""
        try:
            if os.path.exists('bot_data.json'):
                with open('bot_data.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.user_profiles = data.get('user_profiles', {})
                    self.user_stats = data.get('user_stats', {})
                    self.blocked_users = data.get('blocked_users', {})
        except Exception as e:
            logger.error(f"Error loading data: {e}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk command /start"""
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name
        
        # Initialize user stats
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'total_chats': 0,
                'total_messages': 0,
                'joined_date': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
        
        keyboard = [
            [InlineKeyboardButton("🚀 Mulai Chat Anonymous", callback_data="start_chat")],
            [InlineKeyboardButton("👤 Profile Saya", callback_data="my_profile"),
             InlineKeyboardButton("📊 Statistik", callback_data="stats")],
            [InlineKeyboardButton("🏠 Chat Room", callback_data="chat_rooms"),
             InlineKeyboardButton("⚙️ Pengaturan", callback_data="settings")],
            [InlineKeyboardButton("❓ Bantuan", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🎭 <b>Selamat datang di Anonymous Chat Bot!</b>

Halo {user_name}! 👋

🌟 <b>Fitur Unggulan:</b>
• 💬 Chat anonymous 1-on-1
• 🏠 Chat room grup anonymous
• 🎯 Filter berdasarkan minat & usia
• 🎮 Mini games saat chat
• 📊 Statistik personal
• 🛡️ Sistem block & report

Mulai petualangan chat anonymous Anda sekarang!
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk inline keyboard buttons"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        data = query.data
        
        if data == "start_chat":
            await self.show_chat_options(query)
        elif data == "setup_profile":
            await self.setup_profile(query)
        elif data == "my_profile":
            await self.show_profile(query)
        elif data == "stats":
            await self.show_stats(query)
        elif data == "chat_rooms":
            await self.show_chat_rooms(query)
        elif data == "settings":
            await self.show_settings(query)
        elif data == "help":
            await self.show_help(query)
        elif data.startswith("gender_"):
            await self.set_gender(query, data.split("_")[1])
        elif data.startswith("age_"):
            await self.set_age_group(query, data.split("_")[1])
        elif data.startswith("interest_"):
            await self.toggle_interest(query, data.split("_")[1])
        elif data == "find_partner":
            await self.find_chat_partner(query)
        elif data == "end_chat":
            await self.end_current_chat(query)
        elif data == "next_partner":
            await self.next_partner(query)
        elif data == "report_user":
            await self.report_user(query)
        elif data == "block_user":
            await self.block_current_partner(query)
        elif data.startswith("room_"):
            await self.join_chat_room(query, data.split("_")[1])

    async def show_chat_options(self, query):
        """Tampilkan opsi chat"""
        user_id = str(query.from_user.id)
        
        if user_id in self.active_chats:
            partner_id = self.active_chats[user_id]
            keyboard = [
                [InlineKeyboardButton("💬 Lanjut Chat", callback_data="continue_chat")],
                [InlineKeyboardButton("🔄 Cari Partner Baru", callback_data="next_partner")],
                [InlineKeyboardButton("❌ Akhiri Chat", callback_data="end_chat")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "💬 <b>Anda sedang dalam chat!</b>\n\nPilih aksi yang ingin dilakukan:"
        else:
            # Check if user has profile
            if user_id not in self.user_profiles:
                keyboard = [
                    [InlineKeyboardButton("👤 Setup Profile Dulu", callback_data="setup_profile")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                text = "👤 <b>Setup Profile Required</b>\n\nSilakan setup profile Anda terlebih dahulu untuk pengalaman chat yang lebih baik!"
            else:
                keyboard = [
                    [InlineKeyboardButton("🎯 Random Chat", callback_data="find_partner")],
                    [InlineKeyboardButton("🏠 Chat Room", callback_data="chat_rooms")],
                    [InlineKeyboardButton("⚙️ Edit Profile", callback_data="setup_profile")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                text = "🚀 <b>Pilih Mode Chat:</b>\n\n🎯 <b>Random Chat:</b> Chat 1-on-1 dengan stranger\n🏠 <b>Chat Room:</b> Chat grup anonymous"
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def setup_profile(self, query):
        """Setup user profile"""
        user_id = str(query.from_user.id)
        
        keyboard = [
            [InlineKeyboardButton("👨 Pria", callback_data="gender_male"),
             InlineKeyboardButton("👩 Wanita", callback_data="gender_female")],
            [InlineKeyboardButton("⚧️ Lainnya", callback_data="gender_other")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "👤 <b>Setup Profile - Gender</b>\n\nPilih gender Anda:"
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def set_gender(self, query, gender):
        """Set user gender"""
        user_id = str(query.from_user.id)
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        
        self.user_profiles[user_id]['gender'] = gender
        
        keyboard = [
            [InlineKeyboardButton("👶 13-17", callback_data="age_teen"),
             InlineKeyboardButton("🧑 18-25", callback_data="age_young")],
            [InlineKeyboardButton("👨 26-35", callback_data="age_adult"),
             InlineKeyboardButton("👴 36+", callback_data="age_mature")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        gender_text = {"male": "Pria", "female": "Wanita", "other": "Lainnya"}[gender]
        text = f"✅ Gender: {gender_text}\n\n📅 <b>Pilih kelompok usia Anda:</b>"
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def set_age_group(self, query, age_group):
        """Set user age group"""
        user_id = str(query.from_user.id)
        self.user_profiles[user_id]['age_group'] = age_group
        
        interests = ['music', 'movies', 'games', 'sports', 'tech', 'art', 'travel', 'food']
        keyboard = []
        
        for i in range(0, len(interests), 2):
            row = []
            for j in range(2):
                if i + j < len(interests):
                    interest = interests[i + j]
                    emoji = {'music': '🎵', 'movies': '🎬', 'games': '🎮', 'sports': '⚽', 
                           'tech': '💻', 'art': '🎨', 'travel': '✈️', 'food': '🍕'}[interest]
                    row.append(InlineKeyboardButton(f"{emoji} {interest.title()}", 
                                                  callback_data=f"interest_{interest}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("✅ Selesai Setup", callback_data="find_partner")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        age_text = {"teen": "13-17", "young": "18-25", "adult": "26-35", "mature": "36+"}[age_group]
        
        if 'interests' not in self.user_profiles[user_id]:
            self.user_profiles[user_id]['interests'] = []
        
        text = f"✅ Usia: {age_text}\n\n🎯 <b>Pilih minat Anda:</b>\n(Bisa pilih lebih dari satu)"
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def toggle_interest(self, query, interest):
        """Toggle user interest"""
        user_id = str(query.from_user.id)
        
        if 'interests' not in self.user_profiles[user_id]:
            self.user_profiles[user_id]['interests'] = []
        
        if interest in self.user_profiles[user_id]['interests']:
            self.user_profiles[user_id]['interests'].remove(interest)
        else:
            self.user_profiles[user_id]['interests'].append(interest)
        
        # Refresh the interest selection page
        interests = ['music', 'movies', 'games', 'sports', 'tech', 'art', 'travel', 'food']
        keyboard = []
        
        for i in range(0, len(interests), 2):
            row = []
            for j in range(2):
                if i + j < len(interests):
                    int_name = interests[i + j]
                    emoji = {'music': '🎵', 'movies': '🎬', 'games': '🎮', 'sports': '⚽', 
                           'tech': '💻', 'art': '🎨', 'travel': '✈️', 'food': '🍕'}[int_name]
                    
                    # Add checkmark if selected
                    if int_name in self.user_profiles[user_id]['interests']:
                        button_text = f"✅ {emoji} {int_name.title()}"
                    else:
                        button_text = f"{emoji} {int_name.title()}"
                    
                    row.append(InlineKeyboardButton(button_text, 
                                                  callback_data=f"interest_{int_name}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("✅ Selesai Setup", callback_data="find_partner")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        age_text = {"teen": "13-17", "young": "18-25", "adult": "26-35", "mature": "36+"}[self.user_profiles[user_id]['age_group']]
        selected_interests = ", ".join([i.title() for i in self.user_profiles[user_id]['interests']]) or "Belum dipilih"
        
        text = f"✅ Usia: {age_text}\n🎯 <b>Minat terpilih:</b> {selected_interests}\n\n<b>Pilih minat Anda:</b>\n(Bisa pilih lebih dari satu)"
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def find_chat_partner(self, query):
        """Cari partner chat"""
        user_id = str(query.from_user.id)
        
        # Save profile
        self.save_data()
        
        # Add to waiting list
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            self.waiting_users[user_id] = {
                'gender': profile.get('gender', 'other'),
                'age_group': profile.get('age_group', 'young'),
                'interests': profile.get('interests', []),
                'joined_wait': datetime.now()
            }
        
        # Try to find a partner
        partner_id = self.match_users(user_id)
        
        if partner_id:
            # Start chat
            await self.start_anonymous_chat(query, user_id, partner_id)
        else:
            keyboard = [
                [InlineKeyboardButton("❌ Batal Mencari", callback_data="start_chat")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = "🔍 <b>Mencari partner chat...</b>\n\n⏳ Mohon tunggu, sedang mencari orang yang cocok dengan Anda!\n\n💡 <b>Tips:</b>\n• Pastikan profile Anda sudah lengkap\n• Semakin banyak minat, semakin mudah match\n• Jam sibuk (19:00-23:00) lebih banyak user online"
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

    def match_users(self, user_id):
        """Match user dengan partner yang cocok"""
        if user_id not in self.waiting_users:
            return None
        
        user_profile = self.waiting_users[user_id]
        best_match = None
        best_score = 0
        
        for waiting_id, waiting_profile in self.waiting_users.items():
            if waiting_id == user_id:
                continue
            
            # Check if users are blocked
            if (user_id in self.blocked_users and waiting_id in self.blocked_users[user_id]) or \
               (waiting_id in self.blocked_users and user_id in self.blocked_users[waiting_id]):
                continue
            
            # Calculate compatibility score
            score = 0
            
            # Age group compatibility
            age_groups = ['teen', 'young', 'adult', 'mature']
            user_age_idx = age_groups.index(user_profile['age_group'])
            waiting_age_idx = age_groups.index(waiting_profile['age_group'])
            
            if abs(user_age_idx - waiting_age_idx) <= 1:
                score += 3
            
            # Interest compatibility
            common_interests = set(user_profile['interests']) & set(waiting_profile['interests'])
            score += len(common_interests) * 2
            
            # Waiting time (prioritize users waiting longer)
            waiting_time = (datetime.now() - waiting_profile['joined_wait']).seconds
            score += min(waiting_time // 60, 10)  # Max 10 points for waiting time
            
            if score > best_score:
                best_score = score
                best_match = waiting_id
        
        if best_match:
            # Remove both users from waiting list
            del self.waiting_users[user_id]
            del self.waiting_users[best_match]
            return best_match
        
        return None

    async def start_anonymous_chat(self, query, user_id, partner_id):
        """Mulai chat anonymous"""
        # Set active chats
        self.active_chats[user_id] = partner_id
        self.active_chats[partner_id] = user_id
        
        # Create chat session ID
        chat_id = str(uuid.uuid4())
        self.chat_history[chat_id] = {
            'users': [user_id, partner_id],
            'messages': [],
            'started': datetime.now().isoformat()
        }
        
        # Update stats
        for uid in [user_id, partner_id]:
            if uid in self.user_stats:
                self.user_stats[uid]['total_chats'] += 1
                self.user_stats[uid]['last_active'] = datetime.now().isoformat()
        
        # Create keyboards for both users
        keyboard = [
            [InlineKeyboardButton("🔄 Partner Selanjutnya", callback_data="next_partner"),
             InlineKeyboardButton("❌ Akhiri Chat", callback_data="end_chat")],
            [InlineKeyboardButton("🚫 Block User", callback_data="block_user"),
             InlineKeyboardButton("🚨 Report", callback_data="report_user")],
            [InlineKeyboardButton("🎮 Mini Game", callback_data="start_game")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get partner info (anonymized)
        partner_profile = self.user_profiles.get(partner_id, {})
        partner_age = {"teen": "13-17", "young": "18-25", "adult": "26-35", "mature": "36+"}.get(
            partner_profile.get('age_group', 'young'), "18-25")
        partner_gender = {"male": "👨", "female": "👩", "other": "⚧️"}.get(
            partner_profile.get('gender', 'other'), "⚧️")
        partner_interests = ", ".join([i.title() for i in partner_profile.get('interests', [])]) or "Tidak ada"
        
        text = f"""
🎉 <b>Chat Partner Ditemukan!</b>

👤 <b>Partner Info:</b>
{partner_gender} Usia: {partner_age}
🎯 Minat: {partner_interests}

💬 <b>Mulai chat sekarang!</b>
Ketik pesan apa saja untuk memulai percakapan.

⚠️ <b>Peraturan:</b>
• Bersikaplah sopan dan ramah
• Jangan share info personal
• Hormati privacy partner Anda
• No SPAM, SARA, atau konten 18+

Selamat chatting! 🚀
        """
        
        # Send to both users
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        # Send to partner
        try:
            await query.bot.send_message(
                chat_id=partner_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error sending message to partner {partner_id}: {e}")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk pesan chat"""
        user_id = str(update.effective_user.id)
        
        # Update user stats
        if user_id in self.user_stats:
            self.user_stats[user_id]['total_messages'] += 1
            self.user_stats[user_id]['last_active'] = datetime.now().isoformat()
        
        # Check if user is in active chat
        if user_id in self.active_chats:
            partner_id = self.active_chats[user_id]
            
            # Forward message to partner
            try:
                if update.message.text:
                    await context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.TYPING)
                    await asyncio.sleep(random.uniform(0.5, 1.5))  # Simulate typing delay
                    await context.bot.send_message(
                        chat_id=partner_id,
                        text=f"👤 <b>Anonymous:</b> {update.message.text}",
                        parse_mode=ParseMode.HTML
                    )
                elif update.message.photo:
                    await context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.UPLOAD_PHOTO)
                    await context.bot.send_photo(
                        chat_id=partner_id,
                        photo=update.message.photo[-1].file_id,
                        caption="👤 <b>Anonymous</b> mengirim foto",
                        parse_mode=ParseMode.HTML
                    )
                elif update.message.sticker:
                    await context.bot.send_sticker(
                        chat_id=partner_id,
                        sticker=update.message.sticker.file_id
                    )
                elif update.message.voice:
                    await context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.UPLOAD_VOICE)
                    await context.bot.send_voice(
                        chat_id=partner_id,
                        voice=update.message.voice.file_id,
                        caption="👤 <b>Anonymous</b> mengirim voice note",
                        parse_mode=ParseMode.HTML
                    )
                
                # Add reaction to original message
                reactions = ["👍", "❤️", "😊", "🔥", "👏"]
                reaction = random.choice(reactions)
                await update.message.reply_text(f"{reaction}")
                
            except Exception as e:
                logger.error(f"Error forwarding message: {e}")
                await update.message.reply_text("❌ Pesan tidak dapat dikirim. Partner mungkin sudah offline.")
        else:
            # User not in chat, show main menu
            await self.start_command(update, context)

    async def end_current_chat(self, query):
        """Akhiri chat saat ini"""
        user_id = str(query.from_user.id)
        
        if user_id in self.active_chats:
            partner_id = self.active_chats[user_id]
            
            # Remove from active chats
            del self.active_chats[user_id]
            if partner_id in self.active_chats:
                del self.active_chats[partner_id]
            
            # Notify both users
            keyboard = [
                [InlineKeyboardButton("🚀 Chat Lagi", callback_data="find_partner")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="start_chat")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = "👋 <b>Chat telah berakhir!</b>\n\nTerima kasih sudah menggunakan Anonymous Chat Bot!\n\nMau chat lagi?"
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            # Notify partner
            try:
                await query.bot.send_message(
                    chat_id=partner_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Error notifying partner: {e}")
        else:
            await self.show_chat_options(query)

    async def show_stats(self, query):
        """Tampilkan statistik user"""
        user_id = str(query.from_user.id)
        stats = self.user_stats.get(user_id, {})
        
        total_chats = stats.get('total_chats', 0)
        total_messages = stats.get('total_messages', 0)
        joined_date = stats.get('joined_date', datetime.now().isoformat())
        
        joined = datetime.fromisoformat(joined_date)
        days_active = (datetime.now() - joined).days + 1
        
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali", callback_data="start_chat")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
📊 <b>Statistik Anda</b>

💬 Total Chat: <b>{total_chats}</b>
💌 Total Pesan: <b>{total_messages}</b>
📅 Bergabung: <b>{joined.strftime('%d/%m/%Y')}</b>
⏱️ Hari Aktif: <b>{days_active} hari</b>

🏆 <b>Achievement:</b>
{"🥇 Chatter Expert" if total_chats >= 50 else "🥈 Active Chatter" if total_chats >= 20 else "🥉 Newbie Chatter" if total_chats >= 5 else "🐣 Just Started"}

Keep chatting! 🚀
        """
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def show_help(self, query):
        """Tampilkan bantuan"""
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali", callback_data="start_chat")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """
❓ <b>Bantuan & FAQ</b>

🔸 <b>Cara menggunakan bot:</b>
1. Setup profile terlebih dahulu
2. Pilih "Mulai Chat" untuk mencari partner
3. Chat dengan sopan dan ramah
4. Gunakan tombol untuk kontrol chat

🔸 <b>Fitur utama:</b>
• 💬 Chat anonymous 1-on-1
• 🏠 Group chat rooms
• 🎮 Mini games dalam chat
• 📊 Statistik personal
• 🚫 Block & report system

🔸 <b>Tips untuk match cepat:</b>
• Lengkapi profile Anda
• Pilih beberapa minat
• Chat di jam ramai (19:00-23:00)

🔸 <b>Peraturan:</b>
• Tidak boleh share kontak personal
• Dilarang SPAM, SARA, konten 18+
• Bersikap sopan dan menghormati

🔸 <b>Trouble?</b>
Ketik /start untuk restart bot
        """
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Statistik bot untuk admin"""
        if update.effective_user.id != ADMIN_ID:
            return
        
        total_users = len(self.user_profiles)
        active_chats = len(self.active_chats) // 2
        waiting_users = len(self.waiting_users)
        total_messages = sum(stats.get('total_messages', 0) for stats in self.user_stats.values())
        
        text = f"""
🔧 <b>Admin Statistics</b>

👥 Total Users: {total_users}
💬 Active Chats: {active_chats}
⏳ Waiting Users: {waiting_users}
📨 Total Messages: {total_messages}

💾 Data saved to: bot_data.json
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

    def run(self):
        """Jalankan bot"""
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("admin", self.admin_stats))
        
        # Callback handlers
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Message handlers
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.message_handler
        ))
        application.add_handler(MessageHandler(
            filters.PHOTO, self.message_handler
        ))
        application.add_handler(MessageHandler(
            filters.STICKER, self.message_handler
        ))
        application.add_handler(MessageHandler(
            filters.VOICE, self.message_handler
        ))
        
        print("🤖 Bot started successfully!")
        print("📝 Setup instructions:")
        print("1. Buat bot baru di @BotFather")
        print("2. Ganti BOT_TOKEN dengan token Anda")
        print("3. Ganti ADMIN_ID dengan user ID Anda")
        print("4. Install dependencies: pip install python-telegram-bot")
        print("5. Jalankan bot: python bot.py")
        
        # Start polling
        application.run_polling()

    async def show_profile(self, query):
        """Tampilkan profile user"""
        user_id = str(query.from_user.id)
        profile = self.user_profiles.get(user_id, {})
        
        if not profile:
            keyboard = [
                [InlineKeyboardButton("👤 Setup Profile", callback_data="setup_profile")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="start_chat")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("✏️ Edit Profile", callback_data="setup_profile")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="start_chat")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if profile:
            gender = {"male": "👨 Pria", "female": "👩 Wanita", "other": "⚧️ Lainnya"}.get(
                profile.get('gender', 'other'), "⚧️ Lainnya")
            age_group = {"teen": "13-17", "young": "18-25", "adult": "26-35", "mature": "36+"}.get(
                profile.get('age_group', 'young'), "18-25")
            interests = ", ".join([i.title() for i in profile.get('interests', [])]) or "Belum ada"
            
            text = f"""
👤 <b>Profile Anda</b>

{gender}
📅 Usia: {age_group}
🎯 Minat: {interests}

✨ Profile yang lengkap meningkatkan peluang match!
            """
        else:
            text = """
👤 <b>Profile Anda</b>

❌ Profile belum di-setup

Setup profile untuk mendapatkan partner chat yang lebih cocok dengan Anda!
            """
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def show_chat_rooms(self, query):
        """Tampilkan daftar chat rooms"""
        keyboard = [
            [InlineKeyboardButton("💬 General Chat", callback_data="room_general"),
             InlineKeyboardButton("🎮 Gaming Room", callback_data="room_gaming")],
            [InlineKeyboardButton("🎵 Music Lovers", callback_data="room_music"),
             InlineKeyboardButton("🎬 Movie Talk", callback_data="room_movies")],
            [InlineKeyboardButton("💻 Tech Talk", callback_data="room_tech"),
             InlineKeyboardButton("🌍 Travel Stories", callback_data="room_travel")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="start_chat")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """
🏠 <b>Chat Rooms</b>

Pilih room sesuai minat Anda:

💬 <b>General Chat</b> - Obrolan umum
🎮 <b>Gaming Room</b> - Diskusi game
🎵 <b>Music Lovers</b> - Pecinta musik
🎬 <b>Movie Talk</b> - Review & rekomendasi film
💻 <b>Tech Talk</b> - Teknologi & programming
🌍 <b>Travel Stories</b> - Cerita perjalanan

⚠️ <b>Fitur room chat masih dalam development</b>
        """
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def show_settings(self, query):
        """Tampilkan pengaturan"""
        keyboard = [
            [InlineKeyboardButton("👤 Edit Profile", callback_data="setup_profile")],
            [InlineKeyboardButton("🚫 Blocked Users", callback_data="blocked_users")],
            [InlineKeyboardButton("📊 Privacy Settings", callback_data="privacy")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="start_chat")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        user_id = str(query.from_user.id)
        blocked_count = len(self.blocked_users.get(user_id, []))
        
        text = f"""
⚙️ <b>Pengaturan</b>

👤 <b>Profile:</b> Ubah info dasar Anda
🚫 <b>Blocked Users:</b> {blocked_count} user diblock
📊 <b>Privacy:</b> Atur privacy chat

💡 <b>Tips:</b>
• Update profile untuk match yang lebih baik
• Block user yang tidak sopan
• Privacy setting melindungi data Anda
        """
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def next_partner(self, query):
        """Cari partner selanjutnya"""
        user_id = str(query.from_user.id)
        
        # End current chat first
        if user_id in self.active_chats:
            partner_id = self.active_chats[user_id]
            
            # Remove from active chats
            del self.active_chats[user_id]
            if partner_id in self.active_chats:
                del self.active_chats[partner_id]
            
            # Notify partner
            try:
                keyboard = [
                    [InlineKeyboardButton("🚀 Chat Lagi", callback_data="find_partner")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="start_chat")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.bot.send_message(
                    chat_id=partner_id,
                    text="👋 <b>Partner Anda telah berganti chat</b>\n\nMau chat lagi?",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Error notifying partner: {e}")
        
        # Find new partner
        await self.find_chat_partner(query)

    async def block_current_partner(self, query):
        """Block partner saat ini"""
        user_id = str(query.from_user.id)
        
        if user_id not in self.active_chats:
            await query.answer("Tidak ada partner aktif untuk diblock.")
            return
        
        partner_id = self.active_chats[user_id]
        
        # Add to blocked list
        if user_id not in self.blocked_users:
            self.blocked_users[user_id] = []
        
        if partner_id not in self.blocked_users[user_id]:
            self.blocked_users[user_id].append(partner_id)
        
        # End chat
        del self.active_chats[user_id]
        if partner_id in self.active_chats:
            del self.active_chats[partner_id]
        
        # Save data
        self.save_data()
        
        keyboard = [
            [InlineKeyboardButton("🚀 Chat Lagi", callback_data="find_partner")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="start_chat")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🚫 <b>User telah diblock!</b>\n\nAnda tidak akan di-match lagi dengan user ini.\n\nMau chat dengan orang lain?"
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        # Notify partner (without revealing they were blocked)
        try:
            await query.bot.send_message(
                chat_id=partner_id,
                text="👋 <b>Chat telah berakhir!</b>\n\nMau chat lagi?",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying blocked partner: {e}")

    async def report_user(self, query):
        """Report user saat ini"""
        user_id = str(query.from_user.id)
        
        if user_id not in self.active_chats:
            await query.answer("Tidak ada partner aktif untuk direport.")
            return
        
        partner_id = self.active_chats[user_id]
        
        # Send report to admin
        try:
            report_text = f"""
🚨 <b>USER REPORT</b>

Reporter: {user_id}
Reported User: {partner_id}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please investigate this user.
            """
            
            await query.bot.send_message(
                chat_id=ADMIN_ID,
                text=report_text,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error sending report: {e}")
        
        await query.answer("✅ User telah direport ke admin. Terima kasih!")
        
        # Also block the user automatically
        await self.block_current_partner(query)

    async def join_chat_room(self, query, room_id):
        """Join chat room (placeholder)"""
        text = f"""
🏠 <b>Chat Room: {room_id.title()}</b>

🚧 <b>Fitur ini sedang dalam pengembangan!</b>

Akan segera tersedia:
• Group chat anonymous
• Topic-based discussions  
• Room moderators
• Mini games in rooms
• Voice chat rooms

Stay tuned! 🚀
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali", callback_data="chat_rooms")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )


# Main function
if __name__ == "__main__":
    bot = AnonymousChatBot()
    bot.run()
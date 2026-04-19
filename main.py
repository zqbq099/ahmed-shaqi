# -*- coding: utf-8 -*-
# أحمد شاقي - بوت تعبئة إعلانات قطع الغيار
# يعمل على أندرويد باستخدام Kivy
# تم التطوير بواسطة: أنت وأنا

import threading
import json
import os
import time
import requests
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger

# إعدادات DeepSeek API (استخدم مفتاحك الخاص)
DEEPSEEK_API_KEY = "sk-82ea1615ba4c49e2a541bae34c6b7628"  # قم بتغييره

class AhmedShaqiLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=15, **kwargs)
        
        # ضبط اتجاه النصوص لليمين (للعربية)
        self.base_direction = 'rtl'
        
        # عنوان التطبيق
        self.add_widget(Label(text='[b]أحمد شاقي[/b]', markup=True, size_hint_y=0.1, font_size='28sp'))
        self.add_widget(Label(text='بوت تعبئة إعلانات قطع الغيار', size_hint_y=0.08, font_size='16sp'))
        
        # --- إعدادات المنصة ---
        self.add_widget(Label(text='إعدادات المنصة:', size_hint_y=0.06, halign='right'))
        
        self.url_input = TextInput(hint_text='رابط منصتك (مثال: https://منصتك.com)', multiline=False, size_hint_y=0.08)
        self.add_widget(self.url_input)
        
        self.username_input = TextInput(hint_text='اسم المستخدم', multiline=False, size_hint_y=0.08)
        self.add_widget(self.username_input)
        
        self.password_input = TextInput(hint_text='كلمة المرور', password=True, multiline=False, size_hint_y=0.08)
        self.add_widget(self.password_input)
        
        # --- خيارات البحث ---
        self.add_widget(Label(text='خيارات البحث:', size_hint_y=0.06))
        
        # مربع اختيار: البحث عن إعلانات اليوم فقط
        self.today_only_checkbox = CheckBox(active=True, size_hint_x=0.1)
        self.today_only_label = Label(text='البحث عن إعلانات اليوم فقط', size_hint_x=0.9)
        today_box = BoxLayout(orientation='horizontal', size_hint_y=0.06)
        today_box.add_widget(self.today_only_checkbox)
        today_box.add_widget(self.today_only_label)
        self.add_widget(today_box)
        
        # حقل كلمة البحث
        self.search_keyword_input = TextInput(hint_text='كلمة البحث (مثال: قطع غيار سيارات)', multiline=False, size_hint_y=0.08)
        self.add_widget(self.search_keyword_input)
        
        # --- منطقة التحكم ---
        control_box = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=10)
        
        # زر التشغيل
        self.run_btn = Button(text='تشغيل أحمد شاقي', size_hint_x=0.7, background_color=(0.2, 0.6, 1, 1))
        self.run_btn.bind(on_press=self.start_bot)
        control_box.add_widget(self.run_btn)
        
        # زر مسح السجل
        self.clear_btn = Button(text='مسح السجل', size_hint_x=0.3, background_color=(0.5, 0.5, 0.5, 1))
        self.clear_btn.bind(on_press=self.clear_log)
        control_box.add_widget(self.clear_btn)
        
        self.add_widget(control_box)
        
        # --- منطقة عرض السجل (Log) ---
        self.add_widget(Label(text='سجل العمليات:', size_hint_y=0.06, halign='right'))
        
        self.log_scroll = ScrollView(size_hint_y=0.4)
        self.log_label = Label(text='جاهز للعمل...\n', size_hint_y=None, text_size=(None, None), halign='right', valign='top')
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.log_scroll.add_widget(self.log_label)
        self.add_widget(self.log_scroll)
        
    def log(self, message):
        """إضافة رسالة إلى شاشة السجل مع وقت"""
        current_time = datetime.now().strftime("%H:%M:%S")
        current = self.log_label.text
        self.log_label.text = current + f"[{current_time}] {message}\n"
        # التمرير التلقائي للأسفل
        Clock.schedule_once(lambda dt: setattr(self.log_scroll, 'scroll_y', 0), 0.1)
    
    def clear_log(self, instance):
        """مسح محتوى السجل"""
        self.log_label.text = 'تم مسح السجل...\n'
    
    def start_bot(self, instance):
        """تشغيل البوت في خيط منفصل حتى لا تتجمد الواجهة"""
        self.run_btn.disabled = True
        self.run_btn.text = 'يعمل أحمد شاقي...'
        self.log("🚀 بدء المهمة...")
        
        # جمع البيانات المدخلة
        url = self.url_input.text.strip()
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        search_keyword = self.search_keyword_input.text.strip() or "قطع غيار سيارات"
        today_only = self.today_only_checkbox.active
        
        if not url or not username or not password:
            self.log("❌ يجب ملء جميع حقول المنصة")
            self.run_btn.disabled = False
            self.run_btn.text = 'تشغيل أحمد شاقي'
            return
        
        # تشغيل البوت في الخلفية
        threading.Thread(target=self._run_bot, args=(url, username, password, search_keyword, today_only), daemon=True).start()
    
    def _run_bot(self, url, username, password, search_keyword, today_only):
        """المنطق الحقيقي للبوت"""
        try:
            # 1. البحث عن الإعلانات
            self.log(f"🔍 البحث عن '{search_keyword}'...")
            if today_only:
                self.log("📅 البحث عن إعلانات اليوم فقط")
            
            # هنا سنقوم بجلب الإعلانات من المصادر (محاكاة حالياً)
            ads = self._fetch_ads(search_keyword, today_only)
            self.log(f"✅ تم جلب {len(ads)} إعلاناً")
            
            if not ads:
                self.log("⚠️ لا توجد إعلانات جديدة")
                return
            
            # 2. تحليل الإعلانات باستخدام DeepSeek
            self.log("🤖 جاري التحليل بواسطة DeepSeek...")
            parsed_ads = []
            for ad in ads:
                parsed = self._parse_with_deepseek(ad)
                if parsed:
                    parsed_ads.append(parsed)
                    self.log(f"   ✔️ تم تحليل: {parsed.get('العنوان', '')[:30]}...")
            
            self.log(f"✅ تم تحليل {len(parsed_ads)} إعلاناً")
            
            # 3. النشر في المنصة
            self.log("📤 جاري النشر في المنصة...")
            for ad in parsed_ads:
                success = self._post_to_platform(url, username, password, ad)
                if success:
                    self.log(f"   ✔️ تم نشر: {ad.get('العنوان', '')[:30]}...")
                else:
                    self.log(f"   ❌ فشل نشر: {ad.get('العنوان', '')[:30]}...")
            
            self.log("🎉 تمت المهمة بنجاح!")
            
        except Exception as e:
            self.log(f"❌ خطأ: {str(e)}")
        finally:
            Clock.schedule_once(lambda dt: self._enable_button(), 0)
    
    def _fetch_ads(self, keyword, today_only):
        """جلب الإعلانات من المصادر (محاكاة - يمكن تطويرها لاحقاً)"""
        # هذه دالة محاكاة، يمكنك استبدالها بمنطق حقيقي لاحقاً
        # مثل استخدام API لموقع معين أو الزحف (Web Scraping)
        
        # محاكاة لبعض الإعلانات
        mock_ads = [
            "للبيع طقم جنوط مرسيدس 2020 مقاس 18 سعر 1500 درهم في دبي تواصل 0501234567",
            "محرك تويوتا كامري 2018 نظيف جداً ماشي 80 ألف كم فقط السعر 4500 ريال جدة 0567891234",
            "مكيف سيارة كيا سبورتاج 2021 شغال ممتاز السعر 900 ريال الرياض 0554433221",
        ]
        return mock_ads
    
    def _parse_with_deepseek(self, ad_text):
        """تحليل نص الإعلان باستخدام DeepSeek API"""
        if DEEPSEEK_API_KEY == "أدخل_مفتاح_الـ_API_الخاص_بك_هنا":
            # إذا لم يتم تعيين المفتاح، نعيد بيانات وهمية
            return {
                "العنوان": "إعلان تجريبي",
                "السعر": "1000",
                "الوصف": ad_text,
                "رقم_الهاتف": "0500000000",
                "المدينة": "غير محدد",
                "صور": []
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            أنت مساعد خبير في استخراج بيانات إعلانات قطع غيار السيارات.
            من النص التالي، استخرج المعلومات التالية وأرجعها بصيغة JSON صالحة فقط، بدون أي نص إضافي:
            {{
                "العنوان": "اسم القطعة والموديل",
                "السعر": "السعر مع العملة",
                "الوصف": "وصف الحالة",
                "رقم_الهاتف": "رقم التواصل إن وجد",
                "المدينة": "موقع البائع",
                "صور": []
            }}
            إذا لم تجد معلومة، اترك القيمة فارغة.
            
            النص المطلوب تحليله:
            {ad_text}
            """
            
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
            
            response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                # تنظيف الرد
                content = content.strip('`json').strip('`')
                return json.loads(content)
            else:
                self.log(f"⚠️ خطأ في API: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"⚠️ خطأ في DeepSeek: {str(e)}")
            return None
    
    def _post_to_platform(self, url, username, password, ad_data):
        """نشر الإعلان في المنصة (محاكاة - يمكن تطويرها لاحقاً)"""
        # هذه دالة محاكاة، يمكنك استبدالها بمنطق حقيقي لاحقاً
        # مثل استخدام requests لإرسال POST إلى API منصتك
        # أو استخدام WebView للتحكم بالمتصفح
        
        # محاكاة نجاح العملية
        time.sleep(1)  # محاكاة وقت النشر
        return True
    
    def _enable_button(self):
        self.run_btn.disabled = False
        self.run_btn.text = 'تشغيل أحمد شاقي'

class AhmedShaqiApp(App):
    def build(self):
        self.title = 'أحمد شاقي'
        return AhmedShaqiLayout()

if __name__ == '__main__':
    AhmedShaqiApp().run()

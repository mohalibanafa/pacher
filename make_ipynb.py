import json

with open("c:\\Users\\user1\\Desktop\\testes\\patcher\\pacher\\patcher.py", "r", encoding="utf-8") as f:
    code = f.readlines()

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {"id": "guide"},
   "source": [
    "# 🚀 أداة المعالجة السحابية الشاملة (باتشات وضغط)\n",
    "\n",
    "تم تصميم هذا الملف للعمل فوراً على **Google Colab**، مما يوفر عناء تثبيت أي متطلبات ويعتمد كلياً على بيئة التشغيل السحابية.\n",
    "\n",
    "### 🛠️ طريقة الاستخدام:\n",
    "1. انقر على زر التشغيل **▶️ (Run cell)** المجاور لخلية الكود بالأسفل، أو حدد الخلية واضغط على `Ctrl + Enter`.\n",
    "2. سيبدأ التثبيت التلقائي وفحص النظام (لن يستغرق سوى ثوانٍ).\n",
    "3. بمجرد الانتهاء من التثبيت، ستظهر واجهة رسومية تفاعلية (Gradio) **داخل النوت بوك مباشرة**.\n",
    "4. ألصق الروابط المطلوبة (الملف الأصلي والمعدل).\n",
    "5. يمكنك أيضاً فتح الواجهة في متصفح خارجي عبر النقر على الرابط (Public URL) الذي سيظهر في النتائج أدناه."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {"id": "patcher_code"},
   "outputs": [],
   "source": code
  }
 ],
 "metadata": {
  "colab": {
   "provenance": []
  },
  "kernelspec": {
   "display_name": "Python 3",
   "name": "python3"
  },
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 0
}

with open("c:\\Users\\user1\\Desktop\\testes\\patcher\\pacher\\patcher.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

MEDITRACK PRO – START GUIDE (Windows)

1) ZIP extract karein.
2) Extracted MediTrack_Pro folder ko VS Code mein Open Folder karein.
3) VS Code > Terminal > New Terminal kholein.
4) Virtual environment banayein:
   py -m venv .venv
5) Activate karein:
   .venv\Scripts\activate
6) Flask install karein:
   python -m pip install -r requirements.txt
7) App run karein:
   python app.py
8) Browser mein kholein:
   http://127.0.0.1:5000

IMPORTANT:
- Database file meditrack.db pehli baar app.py run karne par automatically banegi.
- Demo records pehli run par add honge.
- Records local laptop par SQLite database mein save hote hain.
- Server stop karne ke liye terminal mein Ctrl+C dabayein.
- Database reset karna ho to server band karke meditrack.db delete karein, phir app dobara run karein.
- Yeh educational inventory/reminder project hai, medical advice ya medicine-safety checker nahi.
- CSS Google Fonts load karne ki koshish karta hai; internet na ho to system fonts use honge.

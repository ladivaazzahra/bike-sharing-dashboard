Dashboard analisis data penyewaan sepeda

submission/
├── dashboard/
│   ├── main_data.csv          
│   ├── main_data_hour.csv     
│   └── dashboard.py           
├── data/
│   ├── day.csv                
│   └── hour.csv               
├── notebook.ipynb             
├── README.md
├── requirements.txt
└── url.txt

running dashboard :
python -m venv venv
# Windows
venv\Scripts\activate

Install Dependencies
pip install -r requirements.txt

jalankan dashboard
streamlit run dashboard/dashboard.py


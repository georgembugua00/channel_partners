import streamlit as st
import streamlit.components.v1 as components
#from sales_exec.leave import leave_roster_calendar
#from sales_exec.user_data import USERS

USERS = {
    "23188032": {
        "role": "Sales Executive", 
        "name": "Stacy",
        "surname": "Mbugua",
        "email": "george@airtel.com",
        "profile_pic": "https://www.shutterstock.com/image-photo/face-portrait-manager-happy-black-260nw-2278812777.jpg",
        "position": "Sales Executive",
        "managing_partner": "Fine Media",
        "cumulative_leave": 21,
        "used_leave": 6
    },
    "1388231": {
        "role": "Manager", 
        "name": "Bryan Osoro", 
        "email": "john@airtel.com",
        "profile_pic": "https://www.shutterstock.com/image-photo/smiling-cheerful-young-adult-african-260nw-1850821510.jpg" ,
        "position": "Zonal Sales Manager",
        "franchise_type": "On Roll"
    },
      "daniel": {
        "name": "Daniel",
        "surname": "Wanganga",
        "position": "Sales Exec",
        "managing_partner": "Sheer Logic",
        "franchise_type": "Franchise",
        "cumulative_leave": 21,
        "used_leave": 4,
        "profile_pic": None,
    },  
}  


# Use a default or dummy user for demo purposes
default_user_key = list(USERS.keys())[0]  # Use first user in USERS dict
user = USERS[default_user_key]

if 'user' not in st.session_state:
    st.session_state.user = user  # Automatically set default user

# --- Home Page ---
slideshow_html = """
<div class="slideshow-container">
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/Send-Money-for%20Free-Web%20Banners.jpg" style="width:100%; height:auto;">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/2GB-@-99-Bob-web-banners.jpg" style="width:100%; height:auto;">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/1GB-@15-Bob-web-banners.jpg" style="width:100%; height:auto;">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/AIRTEL-KENYA_HVC_CAMPAIGN_700_by_700_1.jpg" style="width:100%; height:50%;">
</div>
<div style="text-align:center">
  <span class="dot"></span> 
  <span class="dot"></span> 
  <span class="dot"></span> 
</div>
<script>
let slideIndex = 0;
showSlides();
function showSlides() {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.getElementsByClassName("dot");
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";  
  }
  slideIndex++;
  if (slideIndex > slides.length) {slideIndex = 1}    
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";  
  dots[slideIndex-1].className += " active";
  setTimeout(showSlides, 5000);
}
</script>
<style>
.slideshow-container { max-width: 1000px; position: relative; margin: auto; }
.mySlides { display: none; }
.dot { height: 15px; width: 15px; margin: 0 2px; background-color: #bbb; border-radius: 50%; display: inline-block; }
.active { background-color: #717171; }
.fade { animation-name: fade; animation-duration: 1.5s; }
@keyframes fade { from {opacity: .4} to {opacity: 1} }
</style>
"""

def profile_summary():
    user = st.session_state.user
    remaining_leave = user['cumulative_leave'] - user['used_leave']

    st.html(f"""
    <style>
        .profile-card {{
            background-color: red;
            padding: 20px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 10px rgba(255, 255, 255, 0.1);
        }}
        .profile-img {{
            border-radius: 50%;
            width: 250px;
            height: 250px;
            object-fit: cover;
            margin-right: 20px;
            border: black;
        }}
        .profile-info {{
            flex-grow: 1;
            color:white;
        }}
        .leave-stats {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }}
        .leave-card {{
            background-color: #1a1a1a;
            padding: 10px 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #333;
            color: white;
        }}
        .leave-card.approved {{
            border-left: 4px solid #00cc00;
        }}
    </style>

    <div class="profile-card">
        <img src="{user.get('profile_pic', 'https://media.istockphoto.com/id/1828923094/photo/portrait-of-happy-woman-with-crossed-arms-on-white-background-lawyer-businesswoman-accountant.jpg')}" class="profile-img">
        <div class="profile-info">
            <h2>{user['name']} {user.get('surname', '')}</h2>
            <p>📌 {user.get('position', 'Agent')}</p>
            <p>🏢 {user.get('managing_partner', 'Airtel Kenya')}</p>
            <p>🏷️ {user.get('franchise_type', 'Eastleigh')}</p>
            
            <div class="leave-stats">
                <div class="leave-card">
                    <div style="font-size: 1.2em; font-weight: bold;">{user['cumulative_leave']}</div>
                    <div>Cumulative Days</div>
                </div>
                <div class="leave-card">
                    <div style="font-size: 1.2em; font-weight: bold;">{user['used_leave']}</div>
                    <div>Used Days</div>
                </div>
                <div class="leave-card approved">
                    <div style="font-size: 1.2em; font-weight: bold;">{remaining_leave}</div>
                    <div>Remaining Days</div>
                </div>
            </div>
        </div>
    </div>
    """)

# Render
st.header("Channel Partner Management System")
st.markdown("---")
profile_summary()
st.subheader("📢 Latest Offers")
components.html(slideshow_html, height=500)
leave_roster_calendar()

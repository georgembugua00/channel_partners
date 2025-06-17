import streamlit as st
import streamlit.components.v1 as components
from leave import leave_roster_calendar
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
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/Send-Money-for%20Free-Web%20Banners.jpg" alt="Airtel Offer 1">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/2GB-@-99-Bob-web-banners.jpg" alt="Airtel Offer 2">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/1GB-@15-Bob-web-banners.jpg" alt="Airtel Offer 3">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/AIRTEL-KENYA_HVC_CAMPAIGN_700_by_700_1.jpg" alt="Airtel Offer 4">
</div>
<div style="text-align:center; padding: 15px 0;">
  <span class="dot"></span> 
  <span class="dot"></span> 
  <span class="dot"></span> 
  <span class="dot"></span>
</div>

<script>
let slideIndex = 0;
// Using a named function for better clarity and preventing potential issues with setTimeout scope
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
  setTimeout(showSlides, 5000); // Change image every 5 seconds
}

// Initialize slideshow on page load
document.addEventListener('DOMContentLoaded', showSlides);
</script>

<style>
/* Font import for a modern look */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
body { font-family: 'Inter', sans-serif; }

/* Slideshow Container */
.slideshow-container { 
    width: 100%; 
    max-width: 900px; /* Adjusted max-width for a sleeker look */
    position: relative; 
    margin: 20px auto; /* Added margin for spacing */
    overflow: hidden;
    border-radius: 12px; /* Rounded corners for the container */
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4); /* Deeper shadow */
    background-color: #1a1a1a; /* Subtle background for container */
}

/* Slides */
.mySlides { 
    display: none; 
    width: 100%;
    height: auto; /* Ensure images maintain aspect ratio */
    text-align: center;
}

.mySlides img {
    width: 100%; /* Make image fill container */
    height: auto; /* Maintain aspect ratio */
    display: block;
    border-radius: 12px; /* Inherit border-radius or apply separately */
    object-fit: cover; /* Cover the area, cropping if necessary */
}

/* Dots */
.dot { 
    height: 12px; /* Slightly smaller dots */
    width: 12px; 
    margin: 0 4px; /* More spacing between dots */
    background-color: #666; /* Darker grey for inactive dots */
    border-radius: 50%; 
    display: inline-block; 
    transition: background-color 0.4s ease, transform 0.2s ease; /* Smooth transition and slight scale */
    cursor: pointer;
}

.dot.active { 
    background-color: #FF4B4B; /* Airtel red for active dot */
    transform: scale(1.2); /* Slightly larger active dot */
}

.dot:hover {
    background-color: #FF6F6F; /* Lighter red on hover */
}

/* Fade animation */
.fade {
  -webkit-animation-name: fade;
  -webkit-animation-duration: 1.5s;
  animation-name: fade;
  animation-duration: 1.5s;
}

@-webkit-keyframes fade {
  from {opacity: .7} 
  to {opacity: 1}
}

@keyframes fade {
  from {opacity: .7} 1
  to {opacity: 1}
}

/* Responsive adjustments for smaller screens */
@media (max-width: 768px) {
    .slideshow-container {
        margin: 15px auto;
        border-radius: 8px; /* Slightly less rounded corners on mobile */
    }
    .dot {
        height: 10px;
        width: 10px;
        margin: 0 3px;
    }
}
</style>
"""

def profile_summary():
    user = st.session_state.user
    remaining_leave = user['cumulative_leave'] - user['used_leave']

    st.html(f"""
    <style>
        /* General Styling for Inter Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; }}

        /* Profile Card */
        .profile-card {{
            background: linear-gradient(135deg, #FF4B4B 0%, #CC0000 100%); /* Red gradient */
            padding: 30px; /* More padding */
            border-radius: 15px; /* More rounded corners */
            display: flex;
            align-items: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4); /* Deeper, softer shadow */
            flex-wrap: wrap; 
            justify-content: center; 
            width: 100%; 
            box-sizing: border-box; 
            margin-bottom: 30px; /* Space below the card */
            border: 1px solid rgba(255, 255, 255, 0.1); /* Subtle white border */
            transition: transform 0.3s ease-in-out;
        }}
        .profile-card:hover {{
            transform: translateY(-5px); /* Slight lift on hover */
        }}

        /* Profile Image */
        .profile-img {{
            border-radius: 50%;
            width: 180px; /* Slightly smaller for aesthetics */
            height: 180px; 
            object-fit: cover;
            margin-right: 30px; /* More space */
            border: 4px solid #F0F0F0; /* Light border */
            box-shadow: 0 0 0 8px rgba(255, 255, 255, 0.2), 0 0 0 16px rgba(255, 255, 255, 0.1); /* Layered glow effect */
            flex-shrink: 0; 
            max-width: 100%; 
            transition: border-color 0.3s ease;
        }}
        .profile-img:hover {{
            border-color: #FFD700; /* Gold on hover */
        }}

        /* Profile Info */
        .profile-info {{
            flex-grow: 1;
            color: #FFFFFF; /* White text */
            min-width: 250px; /* Ensure readability */
            padding-top: 5px; 
            text-align: left;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3); /* Subtle text shadow */
        }}
        .profile-info h2 {{
            font-size: 2.2em; /* Larger name */
            margin-bottom: 5px;
            font-weight: 700; /* Bold */
            line-height: 1.2;
        }}
        .profile-info p {{
            font-size: 1em; /* Standard text size */
            margin-bottom: 3px;
            opacity: 0.9; /* Slightly faded */
            font-weight: 300; /* Lighter weight */
        }}

        /* Leave Stats Container */
        .leave-stats {{
            display: flex;
            gap: 20px; /* More space between cards */
            margin-top: 25px; /* More space from profile info */
            flex-wrap: wrap; 
            justify-content: center; 
            width: 100%; 
        }}

        /* Individual Leave Cards */
        .leave-card {{
            background-color: rgba(0, 0, 0, 0.3); /* Semi-transparent dark background */
            backdrop-filter: blur(5px); /* Frosted glass effect */
            padding: 15px 20px; /* More padding */
            border-radius: 12px; /* Rounded corners */
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2); /* Lighter border */
            color: #E0E0E0; /* Off-white text */
            flex: 1 1 150px; /* Flex item: grow, shrink, base-width */
            max-width: 180px; /* Max width for individual cards */
            box-sizing: border-box;
            min-width: 120px; 
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); /* Subtle card shadow */
            transition: transform 0.3s ease, background-color 0.3s ease;
        }}
        .leave-card:hover {{
            transform: translateY(-3px); /* Slight lift on hover */
            background-color: rgba(0, 0, 0, 0.4); /* Darker on hover */
        }}
        .leave-card > div:first-child {{
            font-size: 1.8em; /* Larger numbers */
            font-weight: 700; /* Bolder numbers */
            color: #FFFFFF; /* White numbers */
            margin-bottom: 5px;
        }}
        .leave-card > div:last-child {{
            font-size: 0.85em; /* Descriptive text size */
            opacity: 0.8;
        }}
        .leave-card.approved {{
            border-left: 5px solid #00E676; /* Brighter green for approved */
            background-color: rgba(0, 50, 0, 0.4); /* Slightly greenish tint */
        }}
        .leave-card.approved > div:first-child {{
            color: #98FB98; /* Light green for remaining days number */
        }}

        /* Media Queries for smaller screens */
        @media (max-width: 768px) {{
            .profile-card {{
                flex-direction: column; 
                align-items: center; 
                padding: 20px; 
                margin-bottom: 20px;
            }}
            .profile-img {{
                width: 120px; 
                height: 120px; 
                margin-right: 0; 
                margin-bottom: 20px; 
                border: 3px solid #F0F0F0;
                box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.2);
            }}
            .profile-info {{
                text-align: center; 
                width: 100%; 
                min-width: unset; 
            }}
            .profile-info h2 {{
                font-size: 1.8em; 
            }}
            .profile-info p {{
                font-size: 0.9em; 
            }}
            .leave-stats {{
                flex-direction: row; 
                flex-wrap: wrap; 
                justify-content: center; 
                gap: 10px; 
                margin-top: 15px;
            }}
            .leave-card {{
                flex: 1 1 45%; /* Allow 2 cards per row on small screens */
                max-width: 48%; /* Max width to fit two per row */
                padding: 12px 10px; 
                font-size: 0.9em; 
            }}
            .leave-card > div:first-child {{
                font-size: 1.4em; 
            }}
            .leave-card > div:last-child {{
                font-size: 0.8em; 
            }}
        }}

        @media (max-width: 480px) {{
            .leave-stats {{
                flex-direction: column; /* Stack cards fully on very small screens */
                align-items: center; /* Center them */
            }}
            .leave-card {{
                width: 90%; /* Take nearly full width */
                max-width: 250px; /* Cap max width for very narrow screens */
            }}
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
                    <div>{user['cumulative_leave']}</div>
                    <div>Cumulative Days</div>
                </div>
                <div class="leave-card">
                    <div>{user['used_leave']}</div>
                    <div>Used Days</div>
                </div>
                <div class="leave-card approved">
                    <div>{remaining_leave}</div>
                    <div>Remaining Days</div>
                </div>
            </div>
        </div>
    </div>
    """)

# Render Streamlit components
st.set_page_config(layout="wide") # Use wide layout for better spacing

st.html("""
    <style>
    /* Overall app background and font for Streamlit's main content */
    .stApp {
        background-color: #0d0d0d; /* Very dark background */
        color: #F0F0F0; /* Light text */
        font-family: 'Inter', sans-serif;
    }
    .css-1d3f8gq { /* Target Streamlit's main container for padding */
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FF4B4B; /* Airtel red for Streamlit headers */
        font-weight: 700;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    hr {
        border-top: 1px solid rgba(255, 255, 255, 0.1); /* Subtle divider */
    }
    /* Add any other global Streamlit element styling here */
    </style>
""")


st.header("Channel Partner Management System")
st.markdown("---")
profile_summary()
st.subheader("📢 Latest Offers")
# Ensure Streamlit components are rendered correctly below the HTML
components.html(slideshow_html, height=500)
leave_roster_calendar() # Assuming this is another Streamlit component

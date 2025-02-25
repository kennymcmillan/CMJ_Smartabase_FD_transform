import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

# Function to transform the data
@st.cache_data
def transform_data(input_data, selected_testing_type):
    try:
        # Read Excel file from BytesIO object.
        df_input = pd.read_excel(input_data, sheet_name='ForceDecks Test Results', header=6)
    except Exception as e:
        st.error("Error reading excel file: " + str(e))
        return None
    
    # Define the transfer columns
    transfer_columns = [
        "First Name", "Last Name", "Date", "Time", "Jump Type", "Body Weight (N)", "Load",
        "Measuring Option", "Jump", "Effective Drop Height", "Contact Time", "Flight Time",
        "Height(imp)", "Height(tof)", "Peak ECC", "Peak CON", "Vertical Stiffness", 
        "Peak Force (R)", "Peak Force (L)", "Ave ECC Force (R)", "Ave ECC Force (L)",
        "Ave CON Force (R)", "Ave CON Force (L)", "Concentric Duration [ms]",
        "Positive Takeoff Impulse [Ns]", "Force at Zero Velocity [N]", "FlightTime:Eccentric Duration",
        "Contraction Time [ms]", "Eccentric Peak Velocity [m/s]", "Eccentric Deceleration Impulse [Ns]",
        "Countermovement Depth [cm]", "Drop Height [cm]", "Concentric Peak Force [N]", "Testing Type"
    ]
    
    transfer_df = pd.DataFrame(index=df_input.index, columns=transfer_columns)
    
    # 1. Split "Athlete" into "First Name" and "Last Name"
    if "Athlete" in df_input.columns:
        names_split = df_input["Athlete"].astype(str).str.split(" ", n=1, expand=True)
        transfer_df["First Name"] = names_split[0]
        transfer_df["Last Name"] = names_split[1] if names_split.shape[1] > 1 else "N/A"
    else:
        transfer_df["First Name"] = "N/A"
        transfer_df["Last Name"] = "N/A"
        
    # 2. Process "Test Date" into "Date" and "Time"
    if "Test Date" in df_input.columns:
        df_input["Test Date"] = pd.to_datetime(df_input["Test Date"], errors='coerce')
        transfer_df["Date"] = df_input["Test Date"].dt.date
        transfer_df["Time"] = df_input["Test Date"].dt.strftime('%H:%M').astype(str)

    else:
        transfer_df["Date"] = "N/A"
        transfer_df["Time"] = "N/A"
    
    # 3. Set fixed columns
    transfer_df["Jump Type"] = "CMJ"
    transfer_df["Load"] = "BW (hands on hips)"
    transfer_df["Measuring Option"] = "Dual Force Plates"
    
    # 4. Calculate Body Weight (N)
    if "Body Weight [kg]" in df_input.columns:
        transfer_df["Body Weight (N)"] = df_input["Body Weight [kg]"] * 9.81
    else:
        transfer_df["Body Weight (N)"] = "N/A"
    
    # 5. Mapping from input columns for remaining columns
    transfer_df["Jump"] = df_input.get("Trial", "N/A")
    transfer_df["Effective Drop Height"] = df_input.get("Effective Drop [cm]", "N/A")
    transfer_df["Contact Time"] = df_input.get("Contact Time [ms]", "N/A")
    transfer_df["Flight Time"] = df_input.get("Flight Time [ms]", "N/A")
    transfer_df["Height(imp)"] = df_input.get("Jump Height (Imp-Dis) [cm]", "N/A")
    transfer_df["Height(tof)"] = df_input.get("Jump Height (Flight Time) [cm]", "N/A")
    transfer_df["Peak ECC"] = df_input.get("Eccentric Peak Power [W]", "N/A")
    transfer_df["Peak CON"] = df_input.get("Peak Power [W]", "N/A")
    transfer_df["Vertical Stiffness"] = df_input.get("Active Stiffness [N/m]", "N/A")
    transfer_df["Peak Force (R)"] = df_input.get("Takeoff Peak Force (Right) [N]", "N/A")
    transfer_df["Peak Force (L)"] = df_input.get("Takeoff Peak Force (Left) [N]", "N/A")
    transfer_df["Ave ECC Force (R)"] = df_input.get("Eccentric Mean Force (Right) [N]", "N/A")
    transfer_df["Ave ECC Force (L)"] = df_input.get("Eccentric Mean Force (Left) [N]", "N/A")
    transfer_df["Ave CON Force (R)"] = df_input.get("Concentric Mean Force (Right) [N]", "N/A")
    transfer_df["Ave CON Force (L)"] = df_input.get("Concentric Mean Force (Left) [N]", "N/A")
    transfer_df["Concentric Duration [ms]"] = df_input.get("Concentric Duration [ms]", "N/A")
    transfer_df["Positive Takeoff Impulse [Ns]"] = df_input.get("Positive Takeoff Impulse [N s]", "N/A")
    transfer_df["Force at Zero Velocity [N]"] = df_input.get("Force at Zero Velocity [N]", "N/A")
    transfer_df["FlightTime:Eccentric Duration"] = df_input.get("Flight Time:Contraction Time", "N/A")
    transfer_df["Contraction Time [ms]"] = df_input.get("Contraction Time [ms]", "N/A")
    transfer_df["Eccentric Peak Velocity [m/s]"] = df_input.get("Eccentric Peak Velocity [m/s]", "N/A")
    transfer_df["Eccentric Deceleration Impulse [Ns]"] = df_input.get("Eccentric Deceleration Impulse [Ns]", 
                                                  df_input.get("Eccentric Deceleration Impulse [N s]", "N/A"))
    transfer_df["Countermovement Depth [cm]"] = df_input.get("Countermovement Depth [cm]", "N/A")
    transfer_df["Drop Height [cm]"] = df_input.get("Drop Height [cm]", "N/A")
    transfer_df["Concentric Peak Force [N]"] = df_input.get("Concentric Peak Force [N]", "N/A")
    
    # 6. Set Testing Type to the user-selected value for every row
    transfer_df["Testing Type"] = selected_testing_type
    
    transfer_df["Flight Time"] = transfer_df["Flight Time"] /1000
    transfer_df["Height(imp)"] = transfer_df["Height(imp)"] /100
    transfer_df["Height(tof)"] = transfer_df["Height(tof)"] / 100
    transfer_df["Contraction Time [ms]"] =  transfer_df["Contraction Time [ms]"] / 1000
    
    
    return transfer_df

# Function to convert dataframe to CSV for download
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Streamlit app configuration
st.set_page_config(layout="wide")
st.title("ForceDecks CMJ to Smartabase conversion")

# Sidebar controls
st.sidebar.header("Upload and Options")
uploaded_file = st.sidebar.file_uploader("Choose an Excel file", type=["xls", "xlsx"])
testing_type = st.sidebar.selectbox("Select Testing Type", 
                                    ["Performance Testing", "Fatigue Monitoring"])
                                    
if uploaded_file is not None:
    # Transform the data using the user-selected Testing Type
    transformed_df = transform_data(uploaded_file, testing_type)
    
    if transformed_df is not None:
        st.subheader("Transformed DataFrame")
        st.dataframe(transformed_df)
        
        # Prepare CSV for download
        csv = convert_df_to_csv(transformed_df)
        today_str = datetime.today().strftime("%Y_%m_%d")
        file_name = "CMJ_" + today_str + ".csv"
        
        # Place the download button in the sidebar
        st.sidebar.download_button(
            label="Download CSV",
            data=csv,
            file_name=file_name,
            mime="text/csv"
        )
else:
    st.sidebar.info("Upload an Excel file to begin the transformation.")


import pandas as pd
import streamlit as st
import re

# Function to process data for "S-CSCF Subscriber Registered"
def process_data_with_anchor(df):
    # Convert 'Start Time' to datetime
    try:
        df['Start Time'] = pd.to_datetime(df['Start Time'])
    except Exception as e:
        st.warning(f"Could not convert 'Start Time' to datetime. Skipping time filtering. Detailed error: {e}")

    # Filter data on 'Start Time' at 20:00:00 (if conversion was successful)
    if 'Start Time' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Start Time']):
        df_filtered = df[df['Start Time'].dt.time == pd.to_datetime('20:00:00').time()].copy()
    else:
        df_filtered = df.copy()  # If conversion failed, keep all data

    # Extract site name from 'NE Name'
    df_filtered['Site'] = df_filtered['NE Name'].str.extract('(sm1|vis1)', flags=re.IGNORECASE)

    # Get list of available counters
    counters = [col for col in df.columns if '(number)' in col]

    # Let user select the counter
    selected_counter = st.selectbox("Select Counter", counters, key="tab1_counter")

    # Pivot the dataframe
    df_pivot = df_filtered.pivot_table(index='Start Time', columns='Site', values=selected_counter, fill_value=0)

    # Calculate the total
    df_pivot['Total'] = df_pivot['sm1'] + df_pivot['vis1']
    return df_pivot

# Function to process data for "Without Anchor Subscribers"
def process_data_without_anchor(df_without_anchor):
    # Convert 'Start Time' to datetime format
    df_without_anchor['Start Time'] = pd.to_datetime(df_without_anchor['Start Time'])

    # Filter the data to keep only the rows where the time in 'Start Time' is '20:00:00'
    df_filtered_without_anchor = df_without_anchor[df_without_anchor['Start Time'].dt.time == pd.to_datetime('20:00:00').time()].copy()

    # Extract the 'Site' name (sm1 or vis1) from the 'NE Name' column using regular expressions
    df_filtered_without_anchor['Site'] = df_filtered_without_anchor['NE Name'].str.extract('(sm1|vis1)', flags=re.IGNORECASE)
    
    # Get list of available counters
    counters_without_anchor = [col for col in df_without_anchor.columns if '(number)' in col]

    # Let user select the counter
    selected_counter_without_anchor = st.selectbox("Select Counter", counters_without_anchor, key="tab2_counter")

    # Pivot the DataFrame, directly using the 'Number of S-CSCF Registered Users (number)' column
    df_pivot_without_anchor = df_filtered_without_anchor.pivot_table(index='Start Time', columns='Site', values='Number of S-CSCF Registered Users (number)', aggfunc='sum', fill_value=0)

    # Calculate the 'Total' column
    df_pivot_without_anchor['Total'] = df_pivot_without_anchor['sm1'] + df_pivot_without_anchor['vis1']
    return df_pivot_without_anchor

# Function to process data for "APN Based" (UGW)
def process_data_apn_based_ugw(df_ugw):
    # Convert 'Start Time' to datetime
    df_ugw['Start Time'] = pd.to_datetime(df_ugw['Start Time'], format='%m/%d/%Y %H:%M:%S')

    # Filter data on 'Start Time' at 20:00:00
    df_filtered = df_ugw[df_ugw['Start Time'].dt.time == pd.to_datetime('20:00:00').time()].copy()

    # Filter data on 'APN'
    df_ims = df_filtered[df_filtered['APN'].str.contains('ims', case=False)]
    df_internet = df_filtered[df_filtered['APN'].str.contains('internet', case=False)]
    df_data = df_filtered[~df_filtered['APN'].str.contains('ims', case=False)]

    # Add these 3 dataframes to a dictionary
    apn_dfs = {'IMS APN': df_ims, 'DATA APN': df_data, 'Total APN': df_filtered}

    # Iterate over the dictionary
    result_df = pd.DataFrame()
    for apn_type, df_apn in apn_dfs.items():
        # Calculate the sum of all the 4 counters
        total_sum = df_apn.iloc[:, 4:].sum(axis=0)  # Sum across columns (counters)

        # Create a new dataframe with the APN type and the total sum
        temp_df = pd.DataFrame({'APN Type': [apn_type], 'Total': [total_sum.sum()]})  # Sum the counter sums

        # Append the temp_df to the result_df
        result_df = pd.concat([result_df, temp_df], ignore_index=True)

    return result_df

# Function to process data for "APN Based" (CGW) - Placeholder for now
def process_data_apn_based_cgw(df_cgw):
    # Convert 'Start Time' to datetime
    df_cgw['Start Time'] = pd.to_datetime(df_cgw['Start Time'], format='%m/%d/%Y %H:%M:%S')

    # Filter data on 'Start Time' at 20:00:00
    df_filtered = df_cgw[df_cgw['Start Time'].dt.time == pd.to_datetime('20:00:00').time()].copy()

    # Filter data on 'APN'
    df_ims = df_filtered[df_filtered['APN'].str.contains('ims', case=False)]
    df_internet = df_filtered[df_filtered['APN'].str.contains('internet', case=False)]
    df_data = df_filtered[~df_filtered['APN'].str.contains('ims', case=False)]

    # Add these 3 dataframes to a dictionary
    apn_dfs = {'IMS APN': df_ims, 'DATA APN': df_data, 'Total APN': df_filtered}

    # Iterate over the dictionary and calculate totals
    result_df = pd.DataFrame()
    for apn_type, df_apn in apn_dfs.items():
        total_sum = df_apn[['PGW-C 2/3G Maximum simultaneously activated PDP contexts (APN) (number)',
                           'SGW-C maximum simultaneously subscribers (specified APN) (number)',
                           'PGW-C maximum simultaneously active subscribers (specified APN) (number)',
                           'SGW-C and PGW-C combined Maximum simultaneously activated EPS bearers (APN) (number)']].sum(axis=0)

        # Create a new dataframe with the APN type, total sum, and start time
        temp_df = pd.DataFrame({
            'APN Type': [apn_type],
            'Total': [total_sum.sum()],
            'Start Time': [df_filtered['Start Time'].iloc[0]]  # Assuming consistent Start Time
        })

        # Append the temp_df to the result_df
        result_df = pd.concat([result_df, temp_df], ignore_index=True)

    return result_df

# Main Streamlit app
def main():
    st.title('PAYG Data Extraction')

    # Home screen with buttons
    if st.button("Total Subscriber Registered Data Extraction"):
        st.session_state['page'] = "with_anchor"
    if st.button("Without Anchor Subscribers Data Extraction"):
        st.session_state['page'] = "without_anchor"
    if st.button("APN Based Data Extraction"):
        st.session_state['page'] = "apn_based"

    # Initialize session state variable for page navigation
    if 'page' not in st.session_state:
        st.session_state['page'] = "home"
        
        # Page navigation logic
    if st.session_state['page'] == "with_anchor":
        with_anchor_subscribers()
    elif st.session_state['page'] == "without_anchor":
        without_anchor_subscribers()
    elif st.session_state['page'] == "apn_based":
        apn_based_data()

# Function to handle "With Anchor Subscribers" tab
def with_anchor_subscribers():
    st.header("S-CSCF Subscriber Registered Data Extraction")
    uploaded_file_tab1 = st.file_uploader("Upload Excel or CSV file", type=["xlsx", "xls", "csv"], key="tab1_uploader")

    if uploaded_file_tab1 is not None:
        try:
            # Attempt to read as Excel first
            df = pd.read_excel(uploaded_file_tab1, sheet_name='Sheet1', skiprows=7, engine='openpyxl')
        except Exception as e:
            # If Excel reading fails, try reading as CSV
            try:
                df = pd.read_csv(uploaded_file_tab1, skiprows=7)
            except Exception as e:
                st.error(f"Error reading the file: {e}")
                st.stop()

        # Process the data
        df_pivot = process_data_with_anchor(df)

        # Display the results
        st.write("Extracted Data:")
        st.write(df_pivot)

        # Provide download button
        st.download_button(
            label="Download Data as Excel",
            data=df_pivot.to_csv().encode('utf-8'),
            file_name='extracted_data_with_anchor.csv',
            mime='text/csv',
        )

# Function to handle "Without Anchor Subscribers" tab
def without_anchor_subscribers():
    st.header("Without Anchor Subscribers Data Extraction")
    uploaded_file_tab2 = st.file_uploader("Upload Excel or CSV file for Without Anchor Subscribers", type=["xlsx", "xls", "csv"], key="tab2_uploader")

    if uploaded_file_tab2 is not None:
        try:
            # Attempt to read as Excel first
            df_without_anchor = pd.read_excel(uploaded_file_tab2, skiprows=7, engine='openpyxl')
        except:
            # If it fails, try reading as CSV
            df_without_anchor = pd.read_csv(uploaded_file_tab2, skiprows=7)
        
        # Process the data
        df_pivot_without_anchor = process_data_without_anchor(df_without_anchor)

        # Display the results
        st.write("Extracted Data for Non-Anchor Subscribers:")
        st.write(df_pivot_without_anchor)

        # Provide download button
        st.download_button(
            label="Download Data as Excel",
            data=df_pivot_without_anchor.to_csv().encode('utf-8'),
            file_name='extracted_data_without_anchor.csv',
            mime='text/csv',
        )

# Function to handle "APN Based" tab
def apn_based_data():
    st.header("APN Based Data Extraction")

    tab_ugw, tab_cgw = st.tabs(["UGW", "CGW"])

    with tab_ugw:
        st.subheader("UGW Data Extraction")

        # File uploader for each host
        uploaded_file_host2 = st.file_uploader("Upload CSV file for Host 2", type=["csv"], key="host2_uploader")
        uploaded_file_host3 = st.file_uploader("Upload CSV file for Host 3", type=["csv"], key="host3_uploader")
        uploaded_file_host8 = st.file_uploader("Upload CSV file for Host 8", type=["csv"], key="host8_uploader")
        uploaded_file_host9 = st.file_uploader("Upload CSV file for Host 9", type=["csv"], key="host9_uploader")

        if all([uploaded_file_host2, uploaded_file_host3, uploaded_file_host8, uploaded_file_host9]):
            try:
                # Read all uploaded files
                df_host2 = pd.read_csv(uploaded_file_host2, skiprows=7)
                df_host3 = pd.read_csv(uploaded_file_host3, skiprows=7)
                df_host8 = pd.read_csv(uploaded_file_host8, skiprows=7)
                df_host9 = pd.read_csv(uploaded_file_host9, skiprows=7)

                # Concatenate all DataFrames
                df_ugw = pd.concat([df_host2, df_host3, df_host8, df_host9], ignore_index=True)

                # Process the data
                result_df = process_data_apn_based_ugw(df_ugw)

                # Display the results
                st.write("Extracted Data for APN Based (UGW):")
                st.write(result_df)

                # Provide download button
                st.download_button(
                    label="Download Data as Excel",
                    data=result_df.to_csv(index=False).encode('utf-8'),
                    file_name='extracted_data_apn_based_ugw.csv',
                    mime='text/csv',
                )

            except Exception as e:
                st.error(f"Error processing the files: {e}")

    with tab_cgw:
        st.subheader("CGW Data Extraction")
        st.subheader("CGW Data Extraction")
        uploaded_file_cgw = st.file_uploader("Upload CGW XLSX file", type=["xlsx"], key="ugw_uploader")

        if uploaded_file_cgw:
            try:
                df_ugw = pd.read_csv(uploaded_file_cgw, skiprows=7)

                # Process the data
                result_df = process_data_apn_based_cgw(df_ugw)

                # Display the results
                st.write("Extracted Data for APN Based (CGW):")
                st.write(result_df)

                # Provide download button
                st.download_button(
                    label="Download Data as Excel",
                    data=result_df.to_csv(index=False).encode('utf-8'),
                    file_name='extracted_data_apn_based_cgw.csv',
                    mime='text/csv',
                )
            except Exception as e:
                st.error(f"Error processing the file: {e}")

if __name__ == "__main__":
    main()
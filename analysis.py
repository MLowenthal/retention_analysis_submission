import pandas as pan
import matplotlib.pyplot as plotter
import seaborn as sns

data = pan.read_csv('data/dummy_customer_file.csv')

## Data Cleaning
#Part I: Dealing with Null/NaN Values
#1. Remove rows from columns with low volume of NaN/Null to clean data
low_volume_columns = ['oid', 'provider', 'total_charges', 'signup_date', 'is_canceled', 'is_active', 'is_delinquent', 'current_mrr', 'converted']
data = data.dropna(subset=low_volume_columns)

#2. Fill missing values with defaults for high-volume NaN/Null columns
#For missing date columns, we can assume the user either didn't Convert or Cancel, and replace with default NaT
data['conversion_date'].fillna(pan.NaT, inplace=True)
data['cancellation_date'].fillna(pan.NaT, inplace=True)
data['signup_date'].fillna(pan.NaT, inplace=True)

#For missing geo values, replace with 'UNKNOWN' 
data['personal_person_geo_country'].fillna('UNKNOWN', inplace=True)

#Part II: Standardize Data Formatting
#1. Convert all Geo data to Uppercase
data['personal_person_geo_country'] = data['personal_person_geo_country'].str.upper()

#2 Create dict to clean-up issues with Country Name variations
country_mapping = {
    'UNITED STATES OF AMERICA': 'UNITED STATES',
    'UNITED STATES': 'UNITED STATES',
    'UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND': 'UNITED KINGDOM',
    'UNITED KINGDOM': 'UNITED KINGDOM',
    'RUSSIA FEDERATION': 'RUSSIA',
    'KOREA (REPUBLIC OF)': 'SOUTH KOREA',
    'VIET NAM': 'VIETNAM',
    'BOLIVIA (PLURINATIONAL STATE OF)': 'BOLIVIA',
    'TAIWAN, PROVINCE OF CHINA': 'TAIWAN',
    'TÜRKIYE': 'TURKEY',
    'MACEDONIA (FYROM)': 'MACEDONIA',
    'CÔTE D\'IVOIRE': 'IVORY COAST',
    'RÉUNION': 'REUNION',
    'CONGO (DEMOCRATIC REPUBLIC OF THE)': 'CONGO',
    "LAO PEOPLE'S DEMOCRATIC REPUBLIC": 'LAOS',
    'VENEZUELA (BOLIVARIAN REPUBLIC OF)': 'VENEZUELA'
}
data['personal_person_geo_country'] = data['personal_person_geo_country'].replace(country_mapping)

#3 Convert Date columns to date-time for future analysis. Localize timezones to account for any data points that already have TZs
date_columns = ['signup_date', 'conversion_date', 'cancellation_date']
for col in date_columns:
    data[col] = pan.to_datetime(data[col], errors='coerce').dt.tz_localize(None)

#4 Convert all numeric columns to a singular numeric type to avoid analysis issue
data['total_charges'] = pan.to_numeric(data['total_charges'], errors='coerce')
data['current_mrr'] = pan.to_numeric(data['current_mrr'], errors='coerce')

#5 Remove any duplicate rows 
data = data.drop_duplicates()

#6 Remove any rows with inconsistent date data (i.e. conversion before sign-up, cancellation before conversion)
inconsistent_conversion = data[(data['conversion_date'].notna()) & (data['conversion_date'] < data['signup_date'])]
inconsistent_cancellation = data[(data['cancellation_date'].notna()) & (data['cancellation_date'] < data['conversion_date'])]
data = data.drop(inconsistent_conversion.index)
data = data.drop(inconsistent_cancellation.index)


##Data Analysis
#1. How does retention vary by geography? or provider?

#Let's begin by generating a dict that aligns countries in our data set to specific continents, so we can analyze at our geo data at a higher level
continent_mapping = {
    'AFRICA': ['ALGERIA', 'ANGOLA', 'BENIN', 'BOTSWANA', 'BURKINA FASO', 'BURUNDI', 'CABO VERDE', 'CAMEROON', 'CENTRAL AFRICAN REPUBLIC', 'CHAD', 'COMOROS', 'CONGO', 'CONGO, DEMOCRATIC REPUBLIC OF THE', 'DJIBOUTI', 'EGYPT', 'EQUATORIAL GUINEA', 'ERITREA', 'ESWATINI', 'ETHIOPIA', 'GABON', 'GAMBIA', 'GHANA', 'GUINEA', 'GUINEA-BISSAU', 'IVORY COAST', 'KENYA', 'LESOTHO', 'LIBERIA', 'LIBYA', 'MADAGASCAR', 'MALAWI', 'MALI', 'MAURITANIA', 'MAURITIUS', 'MOROCCO', 'MOZAMBIQUE', 'NAMIBIA', 'NIGER', 'NIGERIA', 'RWANDA', 'SENEGAL', 'SEYCHELLES', 'SIERRA LEONE', 'SOMALIA', 'SOUTH AFRICA', 'SOUTH SUDAN', 'SUDAN', 'TANZANIA', 'TOGO', 'TUNISIA', 'UGANDA', 'ZAMBIA', 'ZIMBABWE'],
    'ASIA': ['AFGHANISTAN', 'ARMENIA', 'AZERBAIJAN', 'BAHRAIN', 'BANGLADESH', 'BHUTAN', 'BRUNEI', 'CAMBODIA', 'CHINA', 'CYPRUS', 'GEORGIA', 'INDIA', 'INDONESIA', 'IRAN', 'IRAQ', 'ISRAEL', 'JAPAN', 'JORDAN', 'KAZAKHSTAN', 'KUWAIT', 'KYRGYZSTAN', 'LAOS', 'LEBANON', 'MALAYSIA', 'MALDIVES', 'MONGOLIA', 'MYANMAR', 'NEPAL', 'NORTH KOREA', 'OMAN', 'PAKISTAN', 'PALESTINE', 'PHILIPPINES', 'QATAR', 'SAUDI ARABIA', 'SINGAPORE', 'SOUTH KOREA', 'SRI LANKA', 'SYRIA', 'TAIWAN', 'TAJIKISTAN', 'THAILAND', 'TIMOR-LESTE', 'TURKEY', 'TURKMENISTAN', 'UNITED ARAB EMIRATES', 'UZBEKISTAN', 'VIETNAM', 'YEMEN'],
    'EUROPE': ['ALBANIA', 'ANDORRA', 'ARMENIA', 'AUSTRIA', 'AZERBAIJAN', 'BELARUS', 'BELGIUM', 'BOSNIA AND HERZEGOVINA', 'BULGARIA', 'CROATIA', 'CYPRUS', 'CZECHIA', 'DENMARK', 'ESTONIA', 'FINLAND', 'FRANCE', 'GEORGIA', 'GERMANY', 'GREECE', 'HUNGARY', 'ICELAND', 'IRELAND', 'ITALY', 'KAZAKHSTAN', 'KOSOVO', 'LATVIA', 'LIECHTENSTEIN', 'LITHUANIA', 'LUXEMBOURG', 'MALTA', 'MOLDOVA', 'MONACO', 'MONTENEGRO', 'NETHERLANDS', 'NORTH MACEDONIA', 'NORWAY', 'POLAND', 'PORTUGAL', 'ROMANIA', 'RUSSIA', 'SAN MARINO', 'SERBIA', 'SLOVAKIA', 'SLOVENIA', 'SPAIN', 'SWEDEN', 'SWITZERLAND', 'UKRAINE', 'UNITED KINGDOM'],
    'NORTH AMERICA': ['ANTIGUA AND BARBUDA', 'BAHAMAS', 'BARBADOS', 'BELIZE', 'CANADA', 'COSTA RICA', 'CUBA', 'DOMINICA', 'DOMINICAN REPUBLIC', 'EL SALVADOR', 'GRENADA', 'GUATEMALA', 'HAITI', 'HONDURAS', 'JAMAICA', 'MEXICO', 'NICARAGUA', 'PANAMA', 'SAINT KITTS AND NEVIS', 'SAINT LUCIA', 'SAINT VINCENT AND THE GRENADINES', 'TRINIDAD AND TOBAGO', 'UNITED STATES'],
    'SOUTH AMERICA': ['ARGENTINA', 'BOLIVIA', 'BRAZIL', 'CHILE', 'COLOMBIA', 'ECUADOR', 'GUYANA', 'PARAGUAY', 'PERU', 'SURINAME', 'URUGUAY', 'VENEZUELA'],
    'OCEANIA': ['AUSTRALIA', 'FIJI', 'KIRIBATI', 'MARSHALL ISLANDS', 'MICRONESIA', 'NAURU', 'NEW ZEALAND', 'PALAU', 'PAPUA NEW GUINEA', 'SAMOA', 'SOLOMON ISLANDS', 'TONGA', 'TUVALU', 'VANUATU'],
}

#Then we'll remove rows that haven't converted so they dont skew our conversion/retention data
#We'll also set the cancellation_date for any currently active users to "today" so analysis involving the column doesn't throw errors
data_Q1 = data.copy()
data_Q1 = data_Q1[data_Q1['conversion_date'].notna()]
data_Q1['end_date'] = data_Q1['cancellation_date'].fillna(pan.Timestamp('today'))

# After that we'll create a unified "active months" metric for each user by finding active days, then converting that to months
data_Q1['subscription_duration_days'] = (data_Q1['end_date'] - data_Q1['conversion_date']).dt.days
data_Q1['subscription_duration'] = (data_Q1['subscription_duration_days'] / 30).astype(int)

# Then we will map each row to its associated continent for future analysis using an iterative for loop and dict we created earlier
continent_reverse_mapping = {}
for continent, countries in continent_mapping.items():
    for country in countries:
        continent_reverse_mapping[country] = continent
data_Q1['continent'] = data_Q1['personal_person_geo_country'].map(continent_reverse_mapping)

#Finally we'll remove any N/A or UNKNOWN rows to not skew our analysis
data_Q1 = data_Q1[~data_Q1['continent'].isna()]
data_Q1 = data_Q1[~data_Q1['personal_person_geo_country'].isna()]


# Then we'll begin calculating the average duration a user is retained by country, continent and provider
avg_duration_by_continent = data_Q1.groupby('continent')['subscription_duration'].mean().reset_index()
avg_duration_by_country = data_Q1.groupby('personal_person_geo_country')['subscription_duration'].mean().reset_index()
avg_duration_by_provider = data_Q1.groupby('provider')['subscription_duration'].mean().reset_index()

# In preperation for visualisation, we will rename columns and sort them
avg_duration_by_continent.rename(columns={'subscription_duration': 'avg_subscription_duration'}, inplace=True)
avg_duration_by_provider.rename(columns={'subscription_duration': 'avg_subscription_duration'}, inplace=True)
avg_duration_by_country.rename(columns={'subscription_duration': 'avg_subscription_duration'}, inplace=True)
avg_duration_by_continent = avg_duration_by_continent.sort_values(by='avg_subscription_duration', ascending=False)
avg_duration_by_country = avg_duration_by_country.sort_values(by='avg_subscription_duration', ascending=False)
avg_duration_by_provider = avg_duration_by_provider.sort_values(by='avg_subscription_duration', ascending=False)

# We'll print the average duration by provider given its simple design and size
print("Average subscription duration by provider:")
print(avg_duration_by_provider)


# Finally we'll plot the results for average duration by country and continent for further analysis in our README.md
plotter.figure(figsize=(10, 6))
sns.barplot(x='avg_subscription_duration', y='continent', data=avg_duration_by_continent)
plotter.title('Average Subscription Duration by Continent')
plotter.xlabel('Average Subscription Duration (months)')
plotter.ylabel('Continent')
plotter.show()

plotter.figure(figsize=(12, 8))
sns.barplot(x='avg_subscription_duration', y='personal_person_geo_country', data=avg_duration_by_country)
plotter.title('Average Subscription Duration by Country')
plotter.xlabel('Average Subscription Duration (months)')
plotter.ylabel('Country')
plotter.show()

#2. Is there evidence of revenue expansion at the customer level?

# We'll start by filtering  out users who never converted, given their revenue is non-existant
data_Q2 = data.copy()
data_Q2 = data_Q2[data_Q2['conversion_date'].notna()]

#Then we'll create a unified "active months" metric for each user, and remove any potential outliers who dont have an active months or MRR
data_Q2['end_date'] = data_Q2['cancellation_date'].fillna(pan.Timestamp('today'))
data_Q2['active_days'] = (data_Q2['end_date'] - data_Q2['conversion_date']).dt.days
data_Q2['active_months'] = (data_Q2['active_days'] / 30).astype(int)
data_Q2 = data_Q2[data_Q2['active_months'] > 0]
data_Q2 = data_Q2[data_Q2['current_mrr'] > 0]


#From there we can calculate the "expected" MRR for our users 
# This metric, which is found via total charges/active months will let us know what a users MRR would be
# if it remained consistent across their entire subscription. We can compare this metric to current_mrr to find implied revenue growth
data_Q2['average_monthly_revenue'] = data_Q2['total_charges'] / data_Q2['active_months']

# We can then execute the comparison outlined above and convert it to a percentage
data_Q2['revenue_expansion'] = data_Q2['average_monthly_revenue'] < data_Q2['current_mrr']
revenue_expansion_percentage = data_Q2['revenue_expansion'].mean() * 100


# Finally we can plot if each user saw revenue growth or not to understand what user types and behaviors might
# lead to additional revenue growth over time
plotter.figure(figsize=(10, 6))
sns.scatterplot(x='average_monthly_revenue', y='current_mrr', hue='revenue_expansion', data=data_Q2, palette={True: 'green', False: 'red'})
plotter.title('Average Monthly Revenue vs Current MRR')
plotter.xlabel('Average Monthly Revenue')
plotter.ylabel('Current MRR')
plotter.axline((0, 0), slope=1, color='blue', linestyle='--')
plotter.legend(title='Revenue Expansion', loc='upper left')
plotter.show()

#3 How is retention trending for different starting cohorts?

# We'll start by removing any non-relavent data,
data_Q3 = data.copy()
data_Q3 = data_Q3[data_Q3['conversion_date'].notna()]

# Then we'll generate cohorts month starting points for each row, and establish the number of active months per users
data_Q3['cohort_month'] = data_Q3['conversion_date'].dt.to_period('M')

data_Q3['end_date'] = data_Q3['cancellation_date'].fillna(pan.Timestamp('today'))
last_month = pan.Timestamp('2023-01-31')
data_Q3['active_months'] = data_Q3.apply(
    lambda row: pan.date_range(start=row['conversion_date'], end=min(row['end_date'], last_month), freq='M').to_period('M'),
    axis=1
)

# We'll then explode our data to generate rows for each instance of a user with their active time
# After that we can roll-up these expanded rows to find our cohort sizes and generate our intial matrix 
data_Q3 = data_Q3.explode('active_months')
cohort_sizes = data_Q3.groupby('cohort_month')['oid'].nunique()
retention_matrix = data_Q3.pivot_table(index='cohort_month', columns='active_months', values='oid', aggfunc='nunique', fill_value=0)

# Then we'll normalize the matrix to ensure no swings in data based on cohort size
retention_matrix = retention_matrix.div(cohort_sizes, axis=0)

# Finally we'll remove infinite values and NaNs with 0 for better readability
retention_matrix.replace([float('inf'), -float('inf')], pan.NA, inplace=True)
retention_matrix.fillna(0, inplace=True)

# And then plot our cohort retention matrix to see what our results show
plotter.figure(figsize=(12, 8))
sns.heatmap(retention_matrix, annot=True, fmt='.0%', cmap='coolwarm_r',cbar=False)
plotter.title('Cohort Analysis - Customer Retention')
plotter.ylabel('Cohort Month')
plotter.xlabel('Active Month')
plotter.show()


#4. How does delinquency affect customer retention and revenue?

# We'll start by removing all of the non-relavent rows to our analysis
# and generating monthly subscription rates for all of our users
data_Q4 = data.copy()
data_Q4 = data_Q4[data_Q4['conversion_date'].notna()]

data_Q4['end_date'] = data_Q4['cancellation_date'].fillna(pan.Timestamp('today'))
data_Q4['subscription_duration_days'] = (data_Q4['end_date'] - data_Q4['conversion_date']).dt.days
data_Q4['subscription_duration'] = (data_Q4['subscription_duration_days'] / 30).astype(int)
data_Q5 = data_Q4[data_Q4['subscription_duration'] > 0]

# Then we'll generate calculations for the metrics we care about, split by delinquency status and combine the results for further analysis
avg_duration_by_delinquency = data_Q4.groupby('is_delinquent')['subscription_duration'].mean().reset_index()
avg_total_charges_by_delinquency = data_Q4.groupby('is_delinquent')['total_charges'].mean().reset_index()
avg_mrr_by_delinquency = data_Q4.groupby('is_delinquent')['current_mrr'].mean().reset_index()

delinquency_analysis = avg_duration_by_delinquency.merge(
    avg_total_charges_by_delinquency, on='is_delinquent'
).merge(
    avg_mrr_by_delinquency, on='is_delinquent'
)

# Finally, we'll rename the columns for clarity and plot our results to analyze further
delinquency_analysis.columns = ['Is Delinquent', 'Avg Subscription Duration (months)', 'Avg Total Charges', 'Avg Current MRR']
fig, axes = plotter.subplots(3, 1, figsize=(10, 18))

sns.barplot(x='Is Delinquent', y='Avg Subscription Duration (months)', data=delinquency_analysis, ax=axes[0])
axes[0].set_title('Average Subscription Duration by Delinquency Status')
axes[0].set_ylabel('Avg Subscription Duration (months)')
axes[0].set_xlabel('')

sns.barplot(x='Is Delinquent', y='Avg Total Charges', data=delinquency_analysis, ax=axes[1])
axes[1].set_title('Average Total Charges by Delinquency Status')
axes[1].set_ylabel('Avg Total Charges')
axes[1].set_xlabel('')

sns.barplot(x='Is Delinquent', y='Avg Current MRR', data=delinquency_analysis, ax=axes[2])
axes[2].set_title('Average Current MRR by Delinquency Status')
axes[2].set_ylabel('Avg Current MRR')
axes[2].set_xlabel('')

plotter.tight_layout()
plotter.show()
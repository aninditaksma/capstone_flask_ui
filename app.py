from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

playstore = pd.read_csv('data/googleplaystore.csv')

playstore.drop_duplicates(keep='first', subset = 'App', inplace=True) 

# Delete row 10472 since the value isn't placed in the correct column
playstore.drop([10472], inplace=True)

playstore.Category = playstore.Category.astype('category')

playstore.Installs = playstore.Installs.apply(lambda x: x.replace(',',''))
playstore.Installs = playstore.Installs.apply(lambda x: x.replace('+',''))

# Clean up column Size
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

playstore.Price = playstore.Price.apply(lambda x: x.replace('$',''))
playstore.Price = playstore.Price.astype('float')

# Change data type of column Reviews, Size, and Installs
playstore[['Reviews', 'Size', 'Installs']] = playstore[['Reviews', 'Size', 'Installs']].astype('int')

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

    # Statistic
    top_category = top_category = pd.crosstab (
        index = df2['Category'],
        columns = 'frequency'
    ).sort_values('frequency', ascending=False).reset_index()

    # Dictionary stats are used to show up value box and table
    stats = {
        'most_categories' : top_category['Category'].head(1).to_list()[0],
        'total': sum(top_category['frequency'].head(1)),
        'rev_table' : df2[['Category', 'App', 'Reviews', 'Rating']].groupby(['Category','App']).sum('Reviews').sort_values('Reviews', ascending=False).head(10).reset_index().to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## Bar Plot
    cat_order = df2.groupby('Category').agg({
    'App' : 'count'
        }).rename({'Category':'Total'}, axis=1).sort_values('App', ascending=False).head().reset_index()
    X = cat_order['Category']
    Y = cat_order['App']
    my_colors = ['r','g','b','k','y','m','c']
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    plt.barh(X, Y, color=my_colors)
    plt.savefig('cat_order.png',bbox_inches="tight") 

    # convert png to base64 
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result = str(figdata_png)[2:-1]
    
    ## Scatter Plot
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = playstore['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.scatter(x=X,y=Y, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    X=(playstore['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## Bar Plot Installs
    install = playstore.groupby('Category').agg({
        'Installs' : 'sum'
    }).sort_values('Installs', ascending=False).head().reset_index()
    X = install['Category']
    Y = install['Installs']
    fig = plt.figure(figsize=(7,5))
    fig.add_subplot()
    plt.bar(X,Y)
    plt.xlabel('Category')
    plt.ylabel('Installs')
    plt.savefig('bar_installs.png',bbox_inches='tight')

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]

    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3, result4=result4)

if __name__ == "__main__": 
    app.run(debug=True)

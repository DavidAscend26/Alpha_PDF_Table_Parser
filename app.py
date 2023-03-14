from datetime import datetime

from flask import Flask, render_template, request
import PyPDF2
from pdfquery import PDFQuery
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['pdf_file']
    table_data = {
        'BODILY INJURY': '',
        'OTHER THAN COLLISION': '',
        'UNINSURED MOTORIST': '',
        'GLASS COVERAGE': '',
        'TOTAL PREMIUM FOR EACH AUTO': '',
        'TOTAL PREMIUM': '',
        'POLICY PERIOD': '',
    }
    #values = []
    policy_period = []
    price_pattern = r'\$\s?[\d,]+\.\d{2}'
    pattern = r"\b(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2},\s+\d{4}\b"
    pdf = PDFQuery(file)
    pdf.load(5)#Policy Period
    # Use CSS-like selectors to locate the elements
    text_elements = pdf.pq('LTTextLineHorizontal')
    # Extract the text from the elements
    text = [t.text for t in text_elements]

    for element in text:
        dates = re.findall(pattern, element)
        if len(dates) > 0:
            policy_period.append(element)
    table_data['POLICY PERIOD'] = ['','','',"From: " + policy_period[0] + " to: " + policy_period[1]]
        #dates = re.findall(testpattern, text)

    pdf.load(7)  # Specific fields
    # Use CSS-like selectors to locate the elements
    text_elements = pdf.pq('LTTextLineHorizontal')

    label = pdf.pq('LTTextLineHorizontal:contains("Bodily Injury")')
    left_corner = float(label.attr('x1'))
    bottom_corner = float(label.attr('y0'))
    bodily_injury = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (left_corner, bottom_corner, left_corner+300, bottom_corner+12)).text()
    table_data['BODILY INJURY'] = [bodily_injury, '', '', '']

    total = pdf.pq('LTTextLineHorizontal:contains("TOTAL PREMIUM")')
    total_premium = ""
    if len(total) == 1:
        total_premium = total.text()
    elif len(total) > 1:
        for result in total:
            t = result.text
            if len(t.split(" ")) < 7:
                concept_value = t.split("TOTAL PREMIUM")
                total_premium = concept_value[1]
    table_data['TOTAL PREMIUM'] = ['', '', '', total_premium]

    total_premium_fea = pdf.pq('LTTextLineHorizontal:contains("TOTAL PREMIUM FOR EACH AUTO")')
    matches_tp = re.findall(price_pattern, total_premium_fea.text())
    table_data['TOTAL PREMIUM FOR EACH AUTO'] = ['', matches_tp[0], matches_tp[1], '']

    other_t_c_l = pdf.pq('LTTextLineHorizontal:contains("Other Than Collision Loss")')
    left_corner = float(other_t_c_l.attr('x0'))
    bottom_corner = float(other_t_c_l.attr('y0'))
    right_corner = float(other_t_c_l.attr('x1'))
    other_collision = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (right_corner, bottom_corner, right_corner + 300, bottom_corner + 12)).text()
    #table_data.append(other_collision)
    columns = re.findall(r"AUTO \d+", other_collision)

    below_other = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (left_corner, bottom_corner-12, right_corner, bottom_corner)).text()
    #table_data.append(below_other)
    prices = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (right_corner, bottom_corner-12, right_corner + 200, bottom_corner)).text()
    #table_data.append(prices)
    price_values = re.findall(r"\$ \d+", prices)
    limit_liability = below_other + " : " + columns[0] + " (" + price_values[0] + ") " + columns[1] + " (" + price_values[1] + ")"
    premiums = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (right_corner+200, bottom_corner - 12, right_corner + 500, bottom_corner)).text()
    matches = re.findall(price_pattern , premiums)
    print(matches)
    table_data['OTHER THAN COLLISION'] = [limit_liability, matches[0], matches[1], '']

    uninsured = pdf.pq('LTTextLineHorizontal:contains("C. UNINSURED MOTORISTS ")')
    left_corner = float(uninsured.attr('x1'))
    bottom_corner = float(uninsured.attr('y0'))
    uninsured_m = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (left_corner, bottom_corner, left_corner + 150, bottom_corner + 12)).text()
    if uninsured_m.isalnum():
        table_data['UNINSURED MOTORIST'] = [uninsured_m, '', '', '']
    else:
        table_data['UNINSURED MOTORIST'] = ["NULL", '', '', '']

    glass = pdf.pq('LTTextLineHorizontal:contains("GLASS COVERAGE")')
    if len(glass) > 0:
        table_data['GLASS COVERAGE'] = ['', '', '', "YES"]
    else:
        table_data['GLASS COVERAGE'] = values = ['', '', '', "NO"]
    print(table_data)

    return render_template('index.html', table_data=table_data)

if __name__ == '__main__':
    app.run(debug=True)
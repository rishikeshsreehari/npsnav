from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

FUNDS = [
    {"id": 1, "scheme_code": "SC001", "scheme_name": "Alpha_Growth ", "pfm_name": "PFM A", "nav": 123.45, "return_1y": "8.2%", "return_3y": "24.5%", "return_5y": "42.0%"},
    {"id": 2, "scheme_code": "SC002", "scheme_name": "Beta_Balanced ", "pfm_name": "PFM B", "nav": 98.76, "return_1y": "6.1%", "return_3y": "18.3%", "return_5y": "35.7%"},
    {"id": 3, "scheme_code": "SC003", "scheme_name": "Delta Debt", "pfm_name": "PFM C", "nav": 76.54, "return_1y": "5.0%", "return_3y": "12.9%", "return_5y": "22.1%"},
]
    # Adicione mais fundos conforme necessário

@require_http_methods(["GET", "POST"])
def compare_funds(request):
    if request.method == "POST":
        selected_fund_ids = request.POST.getlist("funds")
        selected_fund_ids = {int(i) for i in selected_fund_ids if i.isdigit()}
        selected_funds = [f for f in FUNDS if f["id"] in selected_fund_ids]
        return render(request, "compare.html", {"funds": selected_funds})

    return render(request, "compare.html", {"selected_funds": selected_funds, "all_funds": FUNDS})
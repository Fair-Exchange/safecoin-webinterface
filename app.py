from flask import Flask, render_template, redirect, flash, request, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from operator import itemgetter
from safecoinrpc import request as saferequest
from customforms import LoginForm
from os import environ, urandom
from functools import wraps
import requests
import sys, json

app = Flask(__name__)
app.secret_key = urandom(16)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin):
    id = "admin"

@login_manager.user_loader
def load_user(user_id):
    return User()

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm(request.form)
    if form.validate():
        if form.username.data != "user" or form.password.data != "pass":
            return render_template('login.html', error=True)
        login_user(User(), remember=form.remember_me.data)

        flash(f'Logged in successfully. {form.remember_me.data}')

        next = request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        # if not is_safe_url(next):
        #     return abort(400)

        return redirect(next or url_for('home'))
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

def exec_command(command, cmdargs={}, autohandle_errors=True):
    def run(f, *args, **kwargs):
        @wraps(f)
        def func(*args, **kwargs):
            try:
                data = saferequest(command, cmdargs)
            except Exception as e:
                app.logger.warning(e)
                return render_template('loading.html', message="Looking for daemon...", refresh=True)
            if autohandle_errors:
                if data["error"]:
                    return render_template('loading.html', message=data["error"]["message"], refresh=True)
                return f(data["result"], *args, **kwargs)
            return f(data, *args, **kwargs)
        return func
    return run

@app.route('/')
@login_required
@exec_command("getnetworkinfo")
@exec_command("getnetworkhashps")
@exec_command("getinfo")
def home(info, hashrate, netinfo):
    if hashrate < 10**3:
        hashrate = f"{hashrate:.2f} Sol/s"
    hashrate = f"{hashrate/10**3:.2f} kSol/s"
    return render_template("home.html", info=info, hr=hashrate, netinfo=netinfo, refresh=True)

@app.route('/wallets', methods=["GET", "POST"])
@login_required
@exec_command("listreceivedbyaddress", {"params": [0, True]})
@exec_command("z_listaddresses")
def wallets(zaddresses, twallets):
    zwallets = [{"address": zw, "amount": saferequest("z_getbalance", {"params": [zw]})["result"]} for zw in zaddresses]

    hideEmptyWallets = request.form.get("hide", 0, type=int)
    if hideEmptyWallets != 0:
        twallets = [tw for tw in twallets if tw["amount"] != 0]
        zwallets = [zw for zw in zwallets if zw["amount"] != 0]

    twallets = sorted(twallets, key=itemgetter('amount'), reverse=True)
    zwallets = sorted(zwallets, key=itemgetter('amount'), reverse=True)

    return render_template("wallets.html", tw=twallets, zw=zwallets, hide=hideEmptyWallets, refresh=False)

@app.route('/wallets/new')
@login_required
@exec_command("getnewaddress")
def newwallet(newaddress):
    return redirect(url_for("wallets"))

@app.route('/wallets/znew')
@login_required
@exec_command("z_getnewaddress")
def newzwallet(newaddress):
    return redirect(url_for("wallets"))

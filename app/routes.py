from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User, Clinic, Shift
from .forms import LoginForm, ShiftForm
from .utils import calculate_cash_end
# app/routes.py
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from flask import send_file
import io

main_bp = Blueprint('main', __name__)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.shift_form'))
        flash('Неверный логин или пароль')
    return render_template('login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main_bp.route('/shift', methods=['GET', 'POST'])
@login_required
def shift_form():
    form = ShiftForm()
    form.clinic_id.choices = [(c.id, c.name) for c in Clinic.query.all()]

    if form.validate_on_submit():
        cash_end = calculate_cash_end(
            form.cash_start.data,
            form.cash_in.data,
            form.incassation.data,
            form.salary.data,
            form.rko.data,
            form.pko.data,
            form.exchange.data
        )

        shift = Shift(
            user_id=current_user.id,
            clinic_id=form.clinic_id.data,
            date=form.date.data,
            shift_number=form.shift_number.data,
            counter_start=form.counter_start.data,
            counter_end=form.counter_end.data,
            cash_in=form.cash_in.data,
            card_in=form.card_in.data,
            qr_in=form.qr_in.data,
            cash_return=form.cash_return.data,
            card_return=form.card_return.data,
            uk_return=form.uk_return.data,
            cash_start=form.cash_start.data,
            cash_end=cash_end,
            incassation=form.incassation.data,
            salary=form.salary.data,
            exchange=form.exchange.data,
            pko=form.pko.data,
            rko=form.rko.data,
            receipt_number=form.receipt_number.data,
            submitted_by=form.submitted_by.data
        )
        db.session.add(shift)
        db.session.commit()
        flash('Смена сохранена!')
        return redirect(url_for('main.shift_form'))
@main_bp.route('/export')
@login_required
def export_excel():
    shifts = Shift.query.filter_by(user_id=current_user.id).order_by(Shift.date).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "ЖКО"

    # Заголовки (как в вашем файле)
    headers = [
        "Дата", "№ смены", "Показания ККТ на начало", "Показания ККТ на конец",
        "НАЛ", "БЕЗНАЛ", "QR", "ВСЕГО", "Возврат Наличными", "Остаток на начало",
        "Остаток на конец", "Инкасация", "Зарплата", "ПКО", "РКО", "Сдал"
    ]
    ws.append(headers)

    # Данные
    for s in shifts:
        ws.append([
            s.date, s.shift_number, s.counter_start, s.counter_end,
            s.cash_in, s.card_in, s.qr_in, 
            s.cash_in + s.card_in + s.qr_in - s.cash_return - s.card_return,
            s.cash_return, s.cash_start, s.cash_end,
            s.incassation, s.salary, s.pko, s.rko, s.submitted_by
        ])

    # Стилизация
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # Отправка файла
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='ЖКО_экспорт.xlsx'
    )
    # Автозаполнение остатка на начало = конец предыдущей смены
    last_shift = Shift.query.filter_by(user_id=current_user.id).order_by(Shift.date.desc()).first()
    if last_shift:
        form.cash_start.data = last_shift.cash_end

    return render_template('shift_form.html', form=form)

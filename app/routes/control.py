import json
import random
import string
import sys

from flask import Blueprint, render_template, request, jsonify, session, redirect
from werkzeug.security import check_password_hash

from app import db, app
from app.helpers.util import app_config

from app.models.reservationmodel import reservation
from app.models.routemodel import routes
from app.models.usersmodel import users
from app.models.ticketmodel import ticket
from app.models.busmodel import bus
from app.models.transactionmodel import transaction
from app.models.locationmodel import location
from app.models.locationmodel import routes as route_location
control_app_route = Blueprint('control_app_route', __name__, template_folder='templates')


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
@control_app_route.route('/control/login_process', methods=['GET', 'POST'])
def login_process():
    message = 'Error Occurred'
    status = False
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        app.logger.info(role)

        if not email:
         message = 'Email is required'
         status=False

        elif not password:
         message = 'Password is required'
         status =False

        else:
             user = users.query.filter_by(email=email).first()
             if user:
                if check_password_hash(user.password, password) and user.role == role:
                    session[role] = True
                    session['id'] = user.id
                    session['email'] = user.email
                    session['fullname'] = user.fullname
                    message = 'Login successful'
                    status = True
    return jsonify({

        'message': message,
        'status': status
    })






@control_app_route.route('/admin/login')
def control_login():
    path = 'Admin Login'
    return render_template('auth/control-login.html', path=path)


@control_app_route.route('/driver/login')
def driver_login():
    path = 'Driver Login'
    return render_template('auth/control-login.html', path=path)
@control_app_route.route('/control/logout')
def control_logout():
    session.pop('admin', None)
    session.pop('id', None)
    session.pop('email', None)
    return redirect('/')
@control_app_route.route('/control/overview')
def control_overview():
    if not session.get('admin') and not session.get('driver'):
        return redirect('/')
    path = 'Control Panel'
    active_route = request.path
    r_count = reservation.query.count()
    route_count = routes.query.count()
    users_count =  users.query.filter_by(role='user').count()
    ticket_count =  ticket.query.count()

    return render_template('dashboard/control/index.html',ticket_count=ticket_count,users_count=users_count, reservation_count=r_count, route_count=route_count,path=path, route=active_route)


@control_app_route.route('/control/reservations/list')
def control_reservations():
    if not session.get('admin') and not session.get('driver'):
        return redirect('/admin/login')
    path = 'Reservations'
    active_route = request.path
    r_list = reservation.query.join(users).all()
    return render_template('dashboard/control/reservations.html', reserve_list=r_list,path=path, route=active_route)
@control_app_route.route('/control/reservations/search')
def control_reservation_search():
    if not session.get('admin') and not session.get('driver'):
        return redirect('/admin/login')
    path = 'Search Reservation'
    active_route = request.path

    return render_template('dashboard/control/reservations-search.html', path=path, route=active_route)

@control_app_route.route('/control/reservations/search_process', methods=['POST','GET'])
def control_reservation_search_process():
    if not session.get('admin') and not session.get('driver'):
        return redirect('/admin/login')
    status= False
    message='Error Occurred'
    data=[]

    if request.method == 'POST':
        reserve_number = request.form['reservation_number']

        if not reserve_number:
            message='Reservation number required'
            status=False
        else:
            reservations = reservation.query.filter(reservation.reservation_number==reserve_number).one()
            if reservations:
                status=True

                message='Result found'

                data = reservations.to_dict()
            else:
               message='No result found'
               status=False
    return jsonify({
        'status':status,
        'message':message,
    'data':data
    })

@control_app_route.route('/control/reservations/search/result', methods=['POST','GET'])
def control_reservation_search_result():
    if not session.get('admin') and not session.get('driver'):
        return redirect('/')
    path = 'Reservation Search Result'
    active_route = request.path
    r_details= ''
    number = request.args.get("number")
    if not "number" in request.args or number == '':
       return redirect('/404')
    else:
      r_details = reservation.query.filter(reservation.reservation_number==number).join(users).join(ticket).first()
      if not r_details:
         return  redirect('/404')
    return render_template('dashboard/control/reservations-search-result.html', path=path, route=active_route, result=r_details)
@control_app_route.route('/control/bus/list')
def control_bus_list():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Bus List'
    active_route = request.path
    b_list = bus.query.join(users).all()

    return render_template('dashboard/control/bus-list.html',bus_list=b_list,path=path, route=active_route)

@control_app_route.route('/control/bus/add')
def control_bus_add():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Add Bus'
    active_route = request.path
    dr_list = users.query.filter(users.role=='driver').all()
    return render_template('dashboard/control/bus-add.html', drivers_list=dr_list, path=path, route=active_route)
@control_app_route.route('/control/bus/add_process', methods=['POST','GET'])
def control_bus_add_process():
    status = False
    message = 'Error Occurred'
    if not session.get('admin'):
        return redirect('/admin/login')
    if request.method == 'POST':
        bus_name = request.form['bus_name']
        capacity = request.form['max_occupancy']
        adult = request.form['adult']
        children = request.form['children']
        driver = request.form['driver']
        desc = request.form['description']
        status = 1
        check_name = bus.query.filter_by(name=bus_name).first()

        if check_name:
            message = 'Bus with number already exist.'
            status= False
        if not bus_name:
            message = 'Bus number is required'
            status= False
        elif not capacity:
            message = 'Maximum occupancy is required'
            status = False
        elif not driver:
            message = 'Driver is required'
            status = False
        elif not adult:
            message = 'Adult is required'
            status = False
        elif not children:
            message = 'Children is required'
            status = False
        elif not desc:
            message = 'Description is required'
            status = False

        else:
            newbus =  bus(name=bus_name,description=desc,max_occupancy=capacity, adult=adult, children=children,driverId=driver,  status=status)
            db.session.add(newbus)
            db.session.commit()
            status = True
            message = 'Bus created.'
    elif request == 'POST':
        message = 'Please fill out the form !'

    return jsonify({
        'message': message,
        'status': status
    })

@control_app_route.route('/control/ticket/list')
def control_ticket_list():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Ticket List'
    active_route = request.path
    # t_list = ticket.query.all()
    t_list = ticket.query.join(users).join(bus).join(routes).all()
    app.logger.info('Ticket Lit')
    return render_template('dashboard/control/ticket-list.html',ticket_list=t_list, path=path,route=active_route)
@control_app_route.route('/control/ticket/add')
def control_ticket_add():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Ticket Add'
    active_route = request.path
    routes_list = routes.query.filter_by(status=1).all()
    bus_list = bus.query.filter_by(status=1).all()
    dr_list = users.query.filter(users.role=='driver').all()
    return render_template('dashboard/control/ticket-add.html',drivers_list=dr_list, bus_list=bus_list,routes_list=routes_list, path=path, route=active_route)

@control_app_route.route('/control/ticket/add_process', methods=['POST','GET'])
def control_ticket_add_process():
    status = False
    message = 'Error Occurred'
    if not session.get('admin'):
        return redirect('/admin/login')
    if request.method == 'POST':
        name = request.form['name']
        fee = request.form['fee']
        available = request.form['available']
        avail_date = request.form['availability_date']
        dept = request.form['departure_time']
        arrival = request.form['arrival_time']
        bus = request.form['bus']
        driver = request.form['driver']
        route = request.form['route']
        desc = request.form['description']
        status = 1
        ticket_number = id_generator()
        if not name:
            message = 'Ticket name is required'
            status= False
        elif not fee:
            message = 'Fee is required'
            status = False
        elif not int(fee):
            message = 'Fee should be number'
            status = False
        elif not available:
            message = 'Is ticket available should be selected'
            status = False
        elif not avail_date:
            message = 'Availability date is required'
            status = False
        elif not dept:
            message = 'Departure time is required'
            status = False
        elif not arrival:
            message = 'Arrival time is required'
            status = False
        elif not bus:
            message = 'Bus is required'
            status = False
        elif not driver:
            message = 'Driver is required'
            status = False
        elif not route:
            message = 'Route is required'
            status = False
        elif not desc:
            message = 'Description is required'
            status = False


        else:
            data =  ticket(name=name,description=desc,fee=fee, ticket_number=ticket_number, routeId=route,busId=bus,available=available, availability_date=avail_date, arrival_datetime=arrival,departure_datetime=dept, driverId=driver, status=status)
            db.session.add(data)
            db.session.commit()
            status = True
            message = 'Ticket created.'
    elif request == 'POST':
        message = 'Please fill out the form !'

    return jsonify({
        'message': message,
        'status': status
    })


@control_app_route.route('/control/routes/list')
def control_routes_list():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Routes List'
    active_route = request.path
    r_list = routes.query.all()
    app.logger.info(r_list)
    return render_template('dashboard/control/route-list.html' ,route_list=r_list, path=path, route=active_route)
@control_app_route.route('/control/routes/add')
def control_routes_add():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Add Route'
    active_route = request.path
    locations = location.query.all()
    return render_template('dashboard/control/route-add.html', locations=locations,path=path, route=active_route)
@control_app_route.route('/control/route/add_process', methods=['POST','GET'])
def control_route_add_process():
    status = False
    message = 'Error Occured'
    if not session.get('admin'):
        return redirect('/admin/login')
    if request.method == 'POST':
        route_name = request.form['route_name']
        start = request.form['start_route']
        end = request.form['end_route']
        desc = request.form['description']
        status = 1

        if not route_name:
            message = 'Route name is required'
            status= False
        elif not start:
            message = 'Start Location is required'
            status = False
        elif not end:
            message = 'End Location is required'
            status = False


        else:
            data =  routes(name=route_name,description=desc,start_routeId=start, end_routeId=end, status=status)
            db.session.add(data)
            db.session.commit()
            status = True
            message = 'Route created.'
    elif request == 'POST':
        message = 'Please fill out the form !'

    return jsonify({
        'message': message,
        'status': status
    })
@control_app_route.route('/control/users')
def control_users():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Users'
    active_route = request.path
    u_list =  users.query.all()
    return render_template('dashboard/control/users.html', users_list=u_list, path=path, route=active_route)
@control_app_route.route('/control/transactions')
def control_transactions():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Transactions'
    active_route = request.path
    t_list = transaction.query.all()
    return render_template('dashboard/control/transactions.html',transaction_list=t_list, path=path, route=active_route)
@control_app_route.route('/control/settings')
def control_settings():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Settings'
    active_route = request.path
    return render_template('dashboard/control/settings.html', path=path, route=active_route)
@control_app_route.route('/control/profile')
def control_profile():
    if not session.get('admin'):
        return redirect('/admin/login')
    path = 'Profile'
    active_route = request.path
    return render_template('dashboard/control/profile.html', path=path, route=active_route)

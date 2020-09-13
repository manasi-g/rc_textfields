from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from userapp.models import UserProfile, Question, Response
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
import random
from datetime import datetime, timedelta
import re
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control


def signup(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('quiz'))
        return render(request, 'userapp/SignUp.html')
    else:
        username = request.POST.get('username')
        user_regex = '^(?=.{6,32}$)(?![_.-])(?!.*[_.-]{2})[a-zA-Z0-9._-]+(?<![_.-])$'
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        phone = request.POST.get('phone')
        f_pass = request.POST.get('f_pass')
        c_pass = request.POST.get('c_pass')
        if re.search(user_regex, username) == None:
            return render(request, 'userapp/SignUp.html', {'message': 'Enter a valid Username.'})
        if str(first_name).isalpha() == False:
            return render(request, 'userapp/SignUp.html', {'message': 'Enter  Correct First Name.'})
        if str(last_name).isalpha() == False:
            return render(request, 'userapp/SignUp.html', {'message': 'Enter Correct Last Name'})
        if re.search(email_regex, email) == None:
            return render(request, 'userapp/SignUp.html', {'message': 'Enter a valid email id.'})
        if (str(phone).isnumeric() == False) | (int(phone) < 5999999999) | (len(str(phone)) != 10):
            return render(request, 'userapp/SignUp.html', {'message': 'Enter Valid Phone number.'})
        if c_pass == f_pass:
            try:
                user = User.objects.get(username=username)
                return render(request, 'userapp/SignUp.html', {'message': 'Username already exists.'})
            except User.DoesNotExist:
                user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                                email=email, password=f_pass)
                profile = UserProfile(user=user, phone=int(phone))
                profile.save()
                auth.login(request, user)
                profile.login_time = request.user.last_login
                profile.predicted_logout_time = profile.login_time + timedelta(seconds=1680)
                profile.save()
                return HttpResponseRedirect(reverse('quiz'))
        return render(request, 'userapp/SignUp.html', {'message': "Passwords don't match"})


def signin(request):
    if request.method == 'GET':
        return render(request, 'userapp/SignIn.html')
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        profile = UserProfile.objects.get(user=user)
        if user is not None:
            if (profile.user_logout == 1):
                return render(request, 'userapp/SignIn.html',
                              {'message': 'You have already attempted the quiz', 'score': profile.current_score})
            if profile.logout_time is not None:
                if (profile.logout_time > profile.predicted_logout_time):
                    return render(request, 'userapp/SignIn.html',
                                  {'message': 'You have already attempted the quiz', 'score': profile.current_score})
            if user.last_login is None:
                auth.login(request, user)
                profile.login_time = datetime.now()
                profile.predicted_logout_time = profile.login_time + timedelta(seconds=1680)
                profile.save()
                return HttpResponseRedirect(reverse('quiz'))
            else:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('quiz'))
        return render(request, 'userapp/SignIn.html', {'message': 'Invalid Credentials.'})


def logout(request):
    user1 = UserProfile.objects.get(user=request.user)
    user1.user_logout = 1
    user1.logout_time = datetime.now()
    user1.save(update_fields=["user_logout", 'logout_time'])
    auth.logout(request)
    if user1.predicted_logout_time < user1.logout_time:
        return render(request, 'userapp/SignIn.html', {'message': 'Time Up!!', 'score': user1.current_score})
    return render(request, 'userapp/SignIn.html',
                  {'message': 'You logged out Successfully.', 'score': user1.current_score})


@never_cache
def quiz(request):
    try:
        if request.user.is_authenticated:
            username = request.user.username
            user = User.objects.get(username=username)
        if request.method == "GET":
            try:
                user_to_get = UserProfile.objects.get(user=user)
                present_time = datetime.now()
                present_time = (present_time.hour * 3600) + (present_time.minute * 60) + (present_time.second)
                end_time = (user_to_get.predicted_logout_time.hour * 3600) + (user_to_get.predicted_logout_time.minute * 60) + (user_to_get.predicted_logout_time.second)
                timer = end_time - present_time
                if timer <= 0:
                    return redirect('logout')
                if user_to_get.no_question_solved >= 10:
                    user_to_get.user_logout = 1
                    user_to_get.logout_time = datetime.now()
                    user_to_get.save(update_fields=["user_logout", 'logout_time'])
                    auth.logout(request)
                    return render(request, 'userapp/SignIn.html',
                              {'message': 'You logged out Successfully.', 'score': user_to_get.current_score})
                if len(user_to_get.question_attempted.split(" ")) >= 2:
                    response_to_get = Response.objects.filter(user=user.id).last()
                    if (response_to_get.attempt_1 == -1 & response_to_get.attempt_2 == -1) | (user_to_get.decision == 1):
                        ques = Question.objects.get(id=user_to_get.current_ques_id)
                        current_score_to_show = user_to_get.current_score
                        sr_no = user_to_get.no_question_solved + 1
                        present_time = datetime.now()
                        present_time = (present_time.hour * 3600) + (present_time.minute * 60) + (present_time.second)
                        end_time = (user_to_get.predicted_logout_time.hour * 3600) + (
                                user_to_get.predicted_logout_time.minute * 60) + (
                                   user_to_get.predicted_logout_time.second)
                        timer = end_time - present_time
                        converted_time = timedelta(seconds=timer)
                        return render(request, 'userapp/quiz.html',
                                  {'question': ques, 'sr': sr_no, 'score': current_score_to_show,
                                   'remain_time': converted_time, 'abc': user_to_get.decision})
                different = 0
                while (different == 0):
                    id1 = random.randint(1, 10)
                    if str(id1) not in user_to_get.question_attempted.split(" "):
                        different = 1
                ques = Question.objects.get(id=id1)
                ques_list = user_to_get.question_attempted.split(" ")
                ques_list.append(id1)
                user_to_get.question_attempted = " ".join(map(str, ques_list))
                user_to_get.current_ques_id = id1
                user_to_get.save(update_fields=["question_attempted", "current_ques_id"])
                response = Response(question=ques, user=user)
                response.save()
                present_time = datetime.now()
                present_time = (present_time.hour * 3600) + (present_time.minute * 60) + (present_time.second)
                end_time = (user_to_get.predicted_logout_time.hour * 3600) + (
                        user_to_get.predicted_logout_time.minute * 60) + (user_to_get.predicted_logout_time.second)
                timer = end_time - present_time
                converted_time = timedelta(seconds=timer)
                current_score_to_show = user_to_get.current_score
                sr_no = user_to_get.no_question_solved + 1
                return render(request, 'userapp/quiz.html', {'question': ques, 'sr': sr_no, 'score': current_score_to_show,
                                                         'remain_time': converted_time, 'abc': user_to_get.decision})
            except Question.DoesNotExist:
                return redirect('quiz')
    except:
        return render(request, 'userapp/SignIn.html', {'message': 'You need to login.'})


@never_cache
def quiz_post(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    user = User.objects.get(username=username)
    if request.method == 'POST':
        user_to_update = UserProfile.objects.get(user=request.user)
        response_to_update = Response.objects.filter(user=user.id).last()
        present_time = datetime.now()
        present_time = (present_time.hour * 3600) + (present_time.minute * 60) + (present_time.second)
        end_time = (user_to_update.predicted_logout_time.hour * 3600) + (user_to_update.predicted_logout_time.minute * 60) + (user_to_update.predicted_logout_time.second)
        timer = end_time - present_time
        if timer <= 0:
            return redirect('logout')
        if user_to_update.decision == 0:
            attempt_1 = request.POST.get("attempt1")
            response_to_update.attempt_1 = attempt_1
            response_to_update.save(update_fields=["attempt_1"])
            if int(attempt_1) == Question.objects.get(id=user_to_update.current_ques_id).correct_ans:
                user_to_update.no_question_solved = user_to_update.no_question_solved + 1
                user_to_update.current_score = user_to_update.current_score + 4
                user_to_update.save(update_fields=["no_question_solved", "current_score"])
                return HttpResponseRedirect(reverse('quiz'))
            else:
                user_to_update.decision = 1
                present_time = datetime.now()
                present_time = (present_time.hour * 3600) + (present_time.minute * 60) + (present_time.second)
                end_time = (user_to_update.predicted_logout_time.hour * 3600) + (user_to_update.predicted_logout_time.minute * 60) + (
                    user_to_update.predicted_logout_time.second)
                timer = end_time - present_time
                converted_time = timedelta(seconds=timer)
                user_to_update.save(update_fields=['current_score', "decision"])
                return render(request, 'userapp/quiz.html',
                              {'question': Question.objects.get(id=user_to_update.current_ques_id),
                               'sr': user_to_update.no_question_solved + 1, 'score': user_to_update.current_score,
                               "remain_time": converted_time, 'abc' :user_to_update.decision, 'attempt1':attempt_1})
        elif user_to_update.decision == 1:
            attempt_2 = request.POST.get("attempt2")
            response_to_update.save(update_fields=["attempt_2"])
            response_to_update.attempt_2 = attempt_2
            user_to_update.decision = 0
            user_to_update.no_question_solved = user_to_update.no_question_solved + 1
            if int(attempt_2) == Question.objects.get(id=user_to_update.current_ques_id).correct_ans:
                user_to_update.current_score = user_to_update.current_score + 2
            else:
                user_to_update.current_score = user_to_update.current_score - 1
            user_to_update.save(update_fields=['current_score', 'no_question_solved', "decision"])
            return HttpResponseRedirect(reverse('quiz'))

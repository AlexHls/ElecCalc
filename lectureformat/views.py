from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
from django.template import loader
from django.utils.datastructures import MultiValueDictKeyError

import matplotlib.pyplot as plt
from matplotlib import pylab
from pylab import *
import matplotlib
import io
import urllib, base64
from PIL import Image
import numpy as np
import lectureformat.scripts as s
import io
from zipfile import ZipFile
import pandas as pd

from .lecture import *
from .models import *

# Create your views here.
def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")


def team(request):
    return render(request, "team.html")


def rechtshinweise(request):
    return render(request, "rechtshinweise.html")


def legalnotice(request):
    return render(request, "legalnotice.html")


def datenschutz(request):
    return render(request, "datenschutz.html")


def privacy(request):
    return render(request, "privacy.html")


def no404(request):
    return render(request, "no404.html")


def calculator_home(request):
    university_list = University.objects.order_by("university_name")

    template = loader.get_template("calculator_home.html")
    context = {
        "university_list": university_list,
    }

    return HttpResponse(template.render(context, request))


def calculator_base_selection(request):
    # Get and save university
    university = get_object_or_404(University, pk=request.POST["universitys"])
    request.session["university"] = university.id

    # Create lists for parameters to be selected
    faculty_list = Faculty.objects.filter(university=university).order_by(
        "faculty_name"
    )
    lecture_hall_list = LectureHall.objects.filter(university=university).order_by(
        "hall_name"
    )
    streaming_list = StreamingService.objects.order_by("streaming_name")
    vod_list = VideoOnDemandService.objects.order_by("vod_name")

    template = loader.get_template("calculator_base_selection.html")
    context = {
        "university": university,
        "faculty_list": faculty_list,
        "lecture_hall_list": lecture_hall_list,
        "streaming_list": streaming_list,
        "vod_list": vod_list,
    }
    return HttpResponse(template.render(context, request))


def calculator_option_selection(request):
    # Get and save answers
    request.session["num"] = request.POST["num_stud"]
    request.session["time"] = request.POST["time"]
    try:
        faculty = get_object_or_404(Faculty, pk=request.POST["facultys"])
        request.session["faculty"] = faculty.id
        faculty_name = faculty.faculty_name
    except:
        raise Http404("No valid faculty found")

    try:
        lecture_hall = get_object_or_404(LectureHall, pk=request.POST["lecture_halls"])
        lecture_hall_name = lecture_hall.hall_name
        request.session["lecture_hall"] = lecture_hall.id
    except:
        request.session["lecture_hall"] = None
        lecture_hall_name = "None"

    try:
        streaming = get_object_or_404(StreamingService, pk=request.POST["streaming"])
        streaming_name = streaming.streaming_name
        request.session["streaming"] = streaming.id
    except:
        request.session["streaming"] = None
        streaming_name = "None"

    try:
        vod = get_object_or_404(VideoOnDemandService, pk=request.POST["vod"])
        vod_name = vod.vod_name
        request.session["vod"] = vod.id
    except:
        request.session["vod"] = None
        vod_name = "None"

    template = loader.get_template("calculator_option_selection.html")
    context = {
        "university": University.objects.get(
            pk=request.session.get("university")
        ).university_name,
        "num": request.session.get("num"),
        "time": request.session.get("time"),
        "faculty": faculty_name,
        "lecture_hall": lecture_hall_name,
        "streaming": streaming_name,
        "vod": vod_name,
    }

    return HttpResponse(template.render(context, request))


options = [
    "random_living",
    "random_devices",
    "beamer",
    "logplot",
    "notransport",
    "showseating",
    "option1",
]


def calculator_result_selection(request):
    # Get option selections an save them
    sampling = request.POST["sampling"]
    request.session["sampling"] = sampling

    template = loader.get_template("calculator_result_selection.html")
    context = {
        "university": University.objects.get(
            pk=request.session.get("university")
        ).university_name,
        "faculty": Faculty.objects.get(pk=request.session.get("faculty")).faculty_name,
        "num": request.session.get("num"),
        "time": request.session.get("time"),
    }
    if request.session.get("lecture_hall") is not None:
        context["lecture_hall"] = LectureHall.objects.get(
            pk=request.session.get("lecture_hall")
        ).hall_name
    else:
        context["lecture_hall"] = "None"
    if request.session.get("streaming") is not None:
        context["streaming"] = StreamingService.objects.get(
            pk=request.session.get("streaming")
        ).streaming_name
    else:
        context["streaming"] = "None"
    if request.session.get("vod") is not None:
        context["vod"] = VideoOnDemandService.objects.get(
            pk=request.session.get("vod")
        ).vod_name
    else:
        context["vod"] = "None"

    context["sampling"] = sampling

    opts = []
    for option in options:
        try:
            tmp = request.POST[option]
            opts.append(tmp)
        except:
            tmp = None
        request.session[option] = tmp

    context["options"] = ", ".join(opts)

    return HttpResponse(template.render(context, request))


def calculator_result(request):

    mode = request.POST["action"]
    if mode == "Offline":
        mode = "offline"
    elif mode == "Online - Streaming":
        mode = "online-streaming"
    elif mode == "Online - VoD":
        mode = "online-vod"
    elif mode == "Hybrid - Streaming":
        mode = "hybrid-streaming"
    elif mode == "Hybrid - VoD":
        mode = "hybrid-vod"
    else:
        raise ValueError("Specified mode not supported")

    university = University.objects.get(pk=request.session.get("university"))
    faculty = Faculty.objects.get(pk=request.session.get("faculty"))
    num_stud = request.session.get("num")
    time = request.session.get("time")
    sampling = request.session.get("sampling")

    context = {
        "university": university.university_name,
        "faculty": faculty.faculty_name,
        "num": num_stud,
        "time": time,
        "sampling": sampling,
        "mode": mode,
    }
    if request.session.get("lecture_hall") is not None:
        lecture_hall = LectureHall.objects.get(pk=request.session.get("lecture_hall"))
        context["lecture_hall"] = lecture_hall.hall_name
    else:
        lecture_hall = None
        context["lecture_hall"] = "None"
    if request.session.get("streaming") is not None:
        streaming = StreamingService.objects.get(pk=request.session.get("streaming"))
        context["streaming"] = streaming.streaming_name
    else:
        streaming = None
        context["streaming"] = "None"
    if request.session.get("vod") is not None:
        vod = VideoOnDemandService.objects.get(pk=request.session.get("vod"))
        context["vod"] = vod.vod_name
    else:
        vod = None
        context["vod"] = "None"

    opts = []
    for option in options:
        if request.session.get(option) is not None:
            opts.append(request.session.get(option))

    context["options"] = ", ".join(opts)

    lecture = Lecture(
        num_stud=int(num_stud),
        hall=lecture_hall,
        streaming=streaming,
        vod=vod,
        university=university,
        faculty=faculty,
        living=None,
        device=None,
        transport=None,
        options=opts,
    )

    lecture.get_consumption(float(time), mode, sampling.lower())

    if "hybrid" in mode:
        context["consumption"] = np.around(lecture.res_cons, 1)[0]
        context["stat_uncertainty"] = np.around(lecture.res_cons_err, 1)[0]
        if "notransport" in context["options"]:
            context["consumption_notransp"] = np.around(lecture.res_cons_notransp, 1)[0]
            context["stat_uncertainty_notransp"] = np.around(
                lecture.res_cons_err_notransp, 1
            )[0]
        else:
            context["consumption_notransp"] = np.around(lecture.res_cons_notransp, 1)
            context["stat_uncertainty_notransp"] = np.around(
                lecture.res_cons_err_notransp, 1
            )
    else:
        context["consumption"] = np.around(lecture.res_cons, 1)
        context["stat_uncertainty"] = np.around(lecture.res_cons_err, 1)
        context["consumption_notransp"] = np.around(lecture.res_cons_notransp, 1)
        context["stat_uncertainty_notransp"] = np.around(
            lecture.res_cons_err_notransp, 1
        )

    if lecture.figure is not None:
        context["figure"] = lecture.figure

    request.session["data"] = lecture.contribs
    request.session["data_std"] = lecture.contribs_std
    request.session["figure"] = lecture.figure

    context["debug_figures"] = []
    for key in list(lecture.debug_figures.keys()):
        context["debug_figures"].append(lecture.debug_figures[key])

    if "hybrid" in mode:
        context["min_stud_online"] = lecture.min_stud_online[0]
        context["min_stud_offline"] = lecture.min_stud_offline[0]
        if "notransport" in context["options"]:
            context["min_stud_online_notransp"] = lecture.min_stud_online_notransp[0]
            context["min_stud_offline_notransp"] = lecture.min_stud_offline_notransp[0]
        else:
            context["min_stud_online_notransp"] = lecture.min_stud_online_notransp
            context["min_stud_offline_notransp"] = lecture.min_stud_offline_notransp
    else:
        context["min_stud_online"] = lecture.min_stud_online
        context["min_stud_offline"] = lecture.min_stud_offline
        context["min_stud_online_notransp"] = lecture.min_stud_online_notransp
        context["min_stud_offline_notransp"] = lecture.min_stud_offline_notransp

    return render(request, "calculator_result.html", context)


def download_data(request):

    contribs = request.session.get("data")
    contribs_std = request.session.get("data_std")
    figure = request.session.get("figure")

    # Split dataframes in online and offline contributions
    # Online
    contribs_online = {
        "Streaming": contribs["Streaming"],
        "VoD": contribs["VoD"],
        "Living": contribs["Living"],
        "Devices": [],
    }
    contribs_online_std = {
        "Streaming": contribs_std["Streaming"],
        "VoD": contribs_std["VoD"],
        "Living": contribs_std["Living"],
        "Devices": [],
    }
    # Offline
    contribs_offline = {
        "Lecture hall": contribs["Lecture hall"],
        "Transportation": contribs["Transportation"],
        "Devices": [],
    }
    contribs_offline_std = {
        "Lecture hall": contribs_std["Lecture hall"],
        "Transportation": contribs_std["Transportation"],
        "Devices": [],
    }
    # Split devices
    for i in range(0, len(contribs["Devices"]), 2):
        contribs_offline["Devices"].append(contribs["Devices"][i])
        contribs_offline_std["Devices"].append(contribs_std["Devices"][i])
        contribs_online["Devices"].append(contribs["Devices"][i + 1])
        contribs_online_std["Devices"].append(contribs_std["Devices"][i + 1])

    dev = [
        contribs["Devices"][i] + contribs["Devices"][i + 1]
        for i in range(0, len(contribs["Devices"]), 2)
    ]
    dev_std = [
        contribs_std["Devices"][i] + contribs_std["Devices"][i + 1]
        for i in range(0, len(contribs_std["Devices"]), 2)
    ]

    contribs["Devices"] = dev
    contribs_std["Devices"] = dev_std

    in_memory = io.BytesIO()
    zf = ZipFile(in_memory, "a")

    df = pd.DataFrame({k: pd.Series(v) for k, v in contribs.items()})
    df_std = pd.DataFrame({k: pd.Series(v) for k, v in contribs_std.items()})

    df_online = pd.DataFrame({k: pd.Series(v) for k, v in contribs_online.items()})
    df_online_std = pd.DataFrame(
        {k: pd.Series(v) for k, v in contribs_online_std.items()}
    )
    df_offline = pd.DataFrame({k: pd.Series(v) for k, v in contribs_offline.items()})
    df_offline_std = pd.DataFrame(
        {k: pd.Series(v) for k, v in contribs_offline_std.items()}
    )

    zf.writestr("consumption_results.csv", df.to_string())
    zf.writestr("consumption_stdev.csv", df_std.to_string())
    zf.writestr("consumption_online.csv", df_online.to_string())
    zf.writestr("consumption_online_stdev.csv", df_online_std.to_string())
    zf.writestr("consumption_offline.csv", df_offline.to_string())
    zf.writestr("consumption_offline_stdev.csv", df_offline_std.to_string())
    zf.writestr("consumption_figure.svg", figure)

    # fix for Linux zip files read in Windows
    for file in zf.filelist:
        file.create_system = 0

    zf.close()
    response = HttpResponse(in_memory.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=results.zip"

    return response

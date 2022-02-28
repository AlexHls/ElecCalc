from django.db import models
from django.core.files.storage import FileSystemStorage

import numpy as np

# Designation of file storage locations
fs = FileSystemStorage(location="data")

# Create your models here.


class University(models.Model):
    def __str__(self):
        return self.university_name

    def get_transport_statistics(self):
        """
        Returns statistic files as np.array.
        If files have not been specified, Gaussian statistic with 10% uncertainty
        will be used instead
        """
        if self.transport_dur_file is not None:
            t_dur_list = np.genfromtxt(self.transport_dur_file)
        else:
            t_dur_list = np.random.normal(
                loc=self.transport_duration,
                scale=0.1 * self.transport_duration,
                size=100,
            )

        # Get list with available MoT for conversion from string to index
        transport_list = Transportation.objects.filter(university=self).order_by(
            "transport_name"
        )
        index_dict = {}
        for i, m in enumerate(transport_list):
            index_dict[m.transport_name] = i
        mot = []
        t_dur = []
        if self.transport_name_file is not None:
            mot_list = np.genfromtxt(self.transport_name_file, dtype=str, delimiter=",")
        else:
            mot_list = [transport_name] * len(t_dur_list)

        for i, e in enumerate(mot_list):
            try:
                mot.append(index_dict[e])
                t_dur.append(t_dur_list[i])
            except KeyError:
                continue

        return np.array(mot), np.array(t_dur)

    university_name = models.CharField("Name of the University/Campus", max_length=200)

    transport_duration = models.FloatField("Time spent to or from university (min)")
    transport_dur_file = models.FileField(
        "Time spent to or from university - statistic file",
        upload_to="data",
        blank=True,
        null=True,
    )

    #    transport_frequency = models.FloatField("Transport frequency (days/week)")
    #    transport_freq_file = models.FileField(
    #        "Transport frequency - statistic file", upload_to="data", blank=True, null=True
    #    )

    transport_name = models.CharField(
        "Most used mean of transport",
        max_length=200,
    )
    transport_name_file = models.FileField(
        "Means of transportation - statistic file",
        upload_to="data",
        blank=True,
        null=True,
    )


class LectureHall(models.Model):
    def __str__(self):
        return self.hall_name

    def get_consumption(self, time, beamer=True):
        """
        Calculates basic consumption without students

        Parameters
        time : float
            Duration of the lecture (min)
        beamer : bool
            Determines if beamer is used or not

        ------
        Return :
        consumption : float
            returns consumption in kWh
        """

        if beamer:
            self.base_consumption = (
                (
                    self.light_blackboard_count * self.light_blackboard_power
                    + self.light_stairs_count * self.light_stairs_power
                    + self.beamer_count * self.beamer_power
                    + self.amplifier_count * self.amplifier_power
                    + self.mic_count * self.mic_power
                    + self.cam_count * self.cam_power
                    + self.other
                )
                * time
                / 60
            )  # Conversion from min to h
        else:
            self.base_consumption = (
                (
                    self.light_blackboard_count * self.light_blackboard_power
                    + self.light_stairs_count * self.light_stairs_power
                    + self.light_general_count * self.light_general_power
                    + self.amplifier_count * self.amplifier_power
                    + self.mic_count * self.mic_power
                    + self.other
                )
                * time
                / 60
            )  # Conversion from min to h
        return self.base_consumption / 1000  # Conversion from Wh to kWh

    university = models.ForeignKey(
        University, on_delete=models.CASCADE, blank=True, null=True
    )

    hall_name = models.CharField("Name of the lecture hall", max_length=200)

    seating_capacity = models.PositiveIntegerField("Number of available seats")
    seating_capacity_distancing = models.PositiveIntegerField(
        "Number of available seats with social distancing"
    )

    light_blackboard_count = models.PositiveIntegerField(
        "Light bulbs: Blackboard - Number of light bulbs"
    )
    light_blackboard_power = models.FloatField(
        "Light bulbs: Blackboard - Power per light bulb (W)"
    )

    light_stairs_count = models.PositiveIntegerField(
        "Light bulbs: Stairs - Number of light bulbs"
    )
    light_stairs_power = models.FloatField(
        "Light bulbs: Stairs - Power per light bulb (W)"
    )
    light_general_count = models.PositiveIntegerField(
        "Light bulbs: General - Number of light bulbs"
    )
    light_general_power = models.FloatField(
        "Light bulbs: General - Power per light bulb (W)"
    )

    beamer_count = models.PositiveIntegerField("Beamer - Number of beamers")
    beamer_power = models.FloatField("Beamer - Power per beamer (W)")

    amplifier_count = models.PositiveIntegerField("Amplifier - Number of amplifiers")
    amplifier_power = models.FloatField("Amplifier - Power per amplifier (W)")

    mic_count = models.PositiveIntegerField("Microphone - Number of microphones")
    mic_power = models.FloatField("Microphone - Power per microphone (W)")

    cam_count = models.PositiveIntegerField("Camera - Number of cameras")
    cam_power = models.FloatField("Camera - Power per camera (W)")

    other = models.FloatField("Other energy consuming sources (W)")


class StreamingService(models.Model):
    def __str__(self):
        return self.streaming_name

    def get_consumption(self, time):
        """
        Calculates basic consumption

        Parameters
        time : float
            Duration of the lecture (min)

        ------
        Return :
        consumption : float
            returns consumption in kWh
        """
        self.base_consumption = (
            (
                self.streaming_access_power
                + self.streaming_router_power
                + self.streaming_core_pergb * self.streaming_core_data * 1000
                # Conversion from kW to W
            )
            * time
            / 60
        )  # Conversion from min to h

        return self.base_consumption / 1000  # Conversion from Wh to kWh

    streaming_name = models.CharField("Name of the streaming service", max_length=200)
    streaming_access_power = models.FloatField("Access - Power (W)")
    streaming_router_power = models.FloatField("Router - Power (W)")
    streaming_core_pergb = models.FloatField(
        "Core network - Energy consumption per GB data consumption (kWh/GB)"
    )
    streaming_core_data = models.FloatField(
        "Core network - Data consumption per hour (GB/h)"
    )


class VideoOnDemandService(models.Model):
    def __str__(self):
        return self.vod_name

    def get_consumption(self, time):
        """
        Calculates basic consumption

        Parameters
        time : float
            Duration of the lecture (min)

        ------
        Return :
        consumption : float
            returns consumption in kWh
        """
        self.base_consumption = (
            (
                self.vod_access_power
                + self.vod_router_power
                + self.vod_core_data * self.vod_core_pergb * 1000
                # Conversion from kW to W
                + self.vod_data_center_data * self.vod_data_center_power * time / 60
                # Conversion from W/h to W
            )
            * time
            / 60
        )  # Conversion from min to h
        return self.base_consumption / 1000  # Conversion from Wh to kWh

    vod_name = models.CharField("Name of the VoD service", max_length=200)
    vod_access_power = models.FloatField("Access - Power (W)")
    vod_router_power = models.FloatField("Router - Power (W)")
    vod_core_pergb = models.FloatField(
        "Core network - Energy consumption per GB data consumption (kWh/GB)"
    )
    vod_core_data = models.FloatField("Core network - Data consumption per hour (GB/h)")
    vod_data_center_power = models.FloatField(
        "Data center - Power per TB data consumption (W/TB)"
    )
    vod_data_center_data = models.FloatField(
        "Data center - Data consumption per hour (TB/h)"
    )


class LivingSituation(models.Model):
    def __str__(self):
        return self.living_name

    def get_consumption(self, time):
        """
        Calculates basic consumption

        Parameters
        time : float
            Duration of the lecture (min)

        ------
        Return :
        consumption : float
            returns consumption in kWh
        """
        self.base_consumption = (
            self.living_num_lights
            * self.living_power
            * time
            / 60
            # Conversion from min to h
        )

        return self.base_consumption / 1000  # Conversion from Wh to kWh

    living_name = models.CharField("Name of the living situation", max_length=200)
    living_num_lights = models.PositiveIntegerField(
        "Number of light bulbs in the study area"
    )
    living_power = models.FloatField("Average power per light bulb (W)")


class ElectronicDevice(models.Model):
    def __str__(self):
        return self.device_name

    def get_consumption(self, time):
        """
        Calculates basic consumption

        Parameters
        time : float
            Duration of the lecture (min)

        ------
        Return :
        consumption : float
            returns consumption in kWh
        """
        self.base_consumption = self.device_power * time / 60

        return self.base_consumption / 1000

    device_name = models.CharField("Name of the electronic device", max_length=200)
    device_power = models.FloatField("Power of the device (W)")


class Transportation(models.Model):
    def __str__(self):
        return self.transport_name

    def get_consumption(self, time):
        """
        Calculates basic consumption

        Parameters
        time : float
            Travel time (min)

        ------
        Return :
        consumption : float
            returns consumption in kWh
        """

        if self.transport_consumption is not None:
            self.base_consumption = (
                self.transport_consumption
                * self.transport_dist
                * time  # This needs to be in min!
            )
        elif self.transport_co_emission is not None:
            self.base_consumption = (
                self.transport_co_emission
                * self.transport_conv_fact
                * self.transport_dist
                * time  # This needs to be in min!
            )
        else:
            raise AttributeError(
                "Neither CO_2 nor consumption available",
                self.transport_name,
                self.transport_consumption,
                self.transport_co_emission,
            )

        return self.base_consumption

    university = models.ForeignKey(
        University, on_delete=models.CASCADE, blank=True, null=True
    )

    transport_name = models.CharField("Name of means of transportation", max_length=200)

    transport_co_emission = models.FloatField(
        "CO_2 Emission (kg/km)", blank=True, null=True
    )
    transport_conv_fact = models.FloatField(
        "Conversion factor from CO_2 emitted to energy consumed (kWh/kg)",
        blank=True,
        null=True,
    )
    transport_dist = models.FloatField(
        "Conversion factor from minutes travelled to kilometers traveled (km/min)",
        blank=True,
        null=True,
    )
    transport_consumption = models.FloatField(
        "Energy consumption per distance (kWh/km)", blank=True, null=True
    )


class Faculty(models.Model):
    def __str__(self):
        return self.faculty_name

    def get_device_type_statistics(self, online):
        """
        Parameters
        -----
        online : bool
            Determines if online of offline statistic is used

        Returns statistic files as np.array.
        If files have not been specified, Gaussian statistic with 10% uncertainty
        will be used instead
        """
        # Get list with available Devices for conversion from string to index
        device_list = ElectronicDevice.objects.order_by("device_name")
        index_dict = {}
        for i, m in enumerate(device_list):
            index_dict[m.device_name] = i
        dev_stat = []
        if online:
            if self.elec_dev_type_file_online is not None:
                dev_str = np.genfromtxt(
                    self.elec_dev_type_file_online, dtype=str, delimiter=","
                )
            else:
                dev_str = [self.elec_dev_type_online]
        else:
            if self.elec_dev_type_file_offline is not None:
                dev_str = np.genfromtxt(
                    self.elec_dev_type_file_offline, dtype=str, delimiter=","
                )
            else:
                dev_str = [self.elec_dev_type_offline]

        for e in dev_str:
            try:
                dev_stat.append(index_dict[e])
            except KeyError:
                continue

        return np.array(dev_stat)

    def get_lecture_statistics(self):
        """
        Calculates lectures per day

        ------
        Return :
        lpw : int
            Lectures per day
        """

        if self.lecture_freq_file is not None:
            # This is only a quick fix, self.lecture_freq_file should
            # return None if not given. TODO
            try:
                lec_pd = np.mean(np.genfromtxt(self.lecture_freq_file))
            except ValueError:
                lec_pd = self.lecture_frequency
        else:
            lec_pd = self.lecture_frequency

        return lec_pd

    university = models.ForeignKey(
        University, on_delete=models.CASCADE, blank=True, null=True
    )

    faculty_name = models.CharField("Faculty name", max_length=200)

    lecture_frequency = models.FloatField(
        "Number of lectures attended on daily average"
    )
    lecture_freq_file = models.FileField(
        "Number of lectures attended on daily average - statistic file",
        upload_to="data",
        blank=True,
        null=True,
    )

    #    online_lec_freq = models.FloatField("Hours per day of watching online lectures")
    #    online_lec_file = models.FileField(upload_to="data", blank=True, null=True)

    #    live_lec = models.FloatField(
    #        "Percentage of online lectured watched live per faculty"
    #    )
    #    live_lec_file = models.FileField(upload_to="data", blank=True, null=True)

    elec_dev_use = models.FloatField("Use of electronic devices (%)")
    elec_dev_use_file = models.FileField(
        "Use of electronic devices - statistic file",
        upload_to="data",
        blank=True,
        null=True,
    )

    #    elec_dev_freq = models.FloatField(
    #        "Frequency of use of electronic devices (h/day)"
    #    )
    #    elec_dev_freq_file = models.FileField(upload_to="data", blank=True, null=True)

    elec_dev_type_online = models.CharField(
        "Most used electronic device (online)",
        max_length=200,
    )
    elec_dev_type_file_online = models.FileField(
        "Electronic device types (online lectures) - statistic file",
        upload_to="data",
        blank=True,
        null=True,
    )

    elec_dev_type_offline = models.CharField(
        "Most used electronic device (offline)",
        max_length=200,
    )
    elec_dev_type_file_offline = models.FileField(
        "Electronic device types (offline lectures) - statistic file",
        upload_to="data",
        blank=True,
        null=True,
    )

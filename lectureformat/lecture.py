import warnings
import io

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy import interpolate
import pandas as pd

from .models import *

try:
    import emcee
except ImportError:
    emcee = None


class Lecture:
    """Lecture class. Creates an object for one single lecture."""

    def __init__(self, num_stud, **kwargs):
        """
        Initialise the lecture object.
        Requires number of students and format. Further information
        can be added via keywords.
        Possible keywords:
        - hall
            LectureHall object
        - streaming
            StreamingService object
        - vod
            VideoOnDemandService object
        - faculty
            Faculty object
        - university
            University object
        - living
            Living_Situation object
        - device
            Electronic_Device object
        - transport
            Transport object
        - options
            List of str conatining all selected options
        All other relevant information will be automatically
        retrieved from the database based on survey statistics

        Parameters
        ----------
        num_stud : int
            Number of students expected to attend the lecture
        """

        # Check if number of students is valid
        if num_stud < 0:
            raise ValueError(
                "Show me a lecture with negative number of students attending"
            )
        else:
            self.num_stud = num_stud

        for key, value in kwargs.items():
            if key == "hall":
                self.hall = value
            elif key == "streaming":
                self.streaming = value
            elif key == "vod":
                self.vod = value
            elif key == "faculty":
                self.faculty = value
            elif key == "university":
                self.university = value
            elif key == "living":
                self.living = value
            elif key == "device":
                self.device = value
            elif key == "transport":
                self.transport = value
            elif key == "options":
                self.options = value
            else:
                warnings.warn("Unrecognized key '%s', ignoring..." % key)

        self.figure = None
        self.contribs = {
            "Streaming": [],
            "VoD": [],
            "Devices": [],
            "Living": [],
            "Lecture hall": [],
            "Transportation": [],
        }
        self.contribs_std = {
            "Streaming": [],
            "VoD": [],
            "Devices": [],
            "Living": [],
            "Lecture hall": [],
            "Transportation": [],
        }
        self.debug_figures = {}

        return

    def get_hybrid_figure(self, grid, cons, cons_std, interp_grid):
        if "notransport" in self.options:
            notrans = 0
            notrans_std = 0

        fig = plt.figure(figsize=[7.5, 4.8])
        p = max(grid)

        def online(x):
            return x

        def onsite(x):
            return p - x

        plt.plot(grid, cons, label="Median")
        plt.fill_between(
            grid, cons + cons_std, cons - cons_std, alpha=0.3, label=r"1$\sigma$"
        )

        # Add different contributions
        for key in self.contribs.keys():
            if key == "Grid":
                continue
            if len(self.contribs[key]) == 0:
                continue

            if key == "Devices":
                # Devices get written twice, so they need to be summed again
                contrib = [
                    self.contribs[key][i] + self.contribs[key][i + 1]
                    for i in range(0, len(self.contribs[key]), 2)
                ]
                contrib_std = [
                    self.contribs_std[key][i] + self.contribs_std[key][i + 1]
                    for i in range(0, len(self.contribs_std[key]), 2)
                ]
                func = interpolate.interp1d(interp_grid, np.array(contrib))
                func_std = interpolate.interp1d(interp_grid, np.sqrt(contrib_std))
            else:
                func = interpolate.interp1d(interp_grid, np.array(self.contribs[key]))
                func_std = interpolate.interp1d(
                    interp_grid, np.sqrt(self.contribs_std[key])
                )
            c = func(grid)
            s = func_std(grid)

            if "notransport" in self.options and key != "Transportation":
                notrans += c
                notrans_std += s**2

            plt.plot(grid, c, label=key)
            plt.fill_between(grid, c + s, c - s, alpha=0.3)

        if "notransport" in self.options:
            plt.plot(grid, notrans, linestyle="--", label="Without tranposrtation")
            plt.fill_between(
                grid,
                notrans + np.sqrt(notrans_std),
                notrans - np.sqrt(notrans_std),
                alpha=0.3,
            )

        if "showseating" in self.options:
            if self.hall.seating_capacity is not None:
                if max(grid) > self.hall.seating_capacity:
                    plt.axvline(
                        onsite(self.hall.seating_capacity),
                        linestyle=":",
                        color="red",
                        label="Maximum seating capacity",
                    )

        # Put a legend to the right of the current axis
        plt.gca().legend(loc="center left", bbox_to_anchor=(1.05, 0.3))

        if "logplot" in self.options:
            plt.ylabel("log(Consumption per lecture) (kWh)")
            plt.yscale("log", nonpositive="clip")
        else:
            plt.ylabel("Consumption per lecture (kWh)")
        plt.xlabel("Number of students joining online")
        plt.grid()

        minind = np.where(cons == min(cons))
        min_cons = cons[minind]
        min_std = cons_std[minind]

        plt.ylim([0.1, plt.gca().get_ylim()[1]])

        secax = plt.gca().secondary_xaxis("top", functions=(online, onsite))
        secax.set_xlabel("Number of students joining on-site")

        plt.tight_layout()

        # these are matplotlib.patch.Patch properties
        props = dict(boxstyle="round", alpha=0.5)

        if "notransport" in self.options:
            min_ind_nt = np.where(notrans == min(notrans))
            min_cons_nt = notrans[min_ind_nt]
            min_std_nt = np.sqrt(notrans_std[min_ind_nt])
            textstr = "Optimal mode:\n- %d students online\n- %d students on-site\n- Total consumption: %.2f $\pm$ %.2f$\,$kWh\n\n" % (
                grid[minind],
                max(grid) - grid[minind],
                min_cons,
                min_std,
            ) + "Without transportation:\n- %d students online\n- %d students on-site\n- Consumption: %.2f $\pm$ %.2f$\,$kWh" % (
                grid[min_ind_nt],
                max(grid) - grid[min_ind_nt],
                min_cons_nt,
                min_std_nt,
            )
        else:
            textstr = (
                "Optimal mode:\n- %d students online\n- %d students on-site\n- Total consumption: %.2f $\pm$ %.2f$\,$kWh"
                % (grid[minind], max(grid) - grid[minind], min_cons, min_std)
            )

        # place a text box in upper left in axes coords
        txt = plt.gca().text(
            1.05,
            1.15,
            textstr,
            transform=plt.gca().transAxes,
            fontsize=14,
            verticalalignment="top",
            bbox=props,
        )

        imgdata = io.StringIO()
        fig.savefig(
            imgdata,
            format="svg",
            bbox_inches="tight",
            bbox_extra_artists=(txt,),
            dpi=600,
        )
        imgdata.seek(0)

        data = imgdata.getvalue()
        return data

    def get_random_living_consumption(
        self, time, living_list, living_random_length=100
    ):
        """
        Gets a randomised value for the consumption of the living arrangements
        """
        cons = []
        l_cons = []
        for l in living_list:
            l_cons.append(l.get_consumption(time))
        indices = np.arange(len(l_cons))
        for i in range(living_random_length):
            rnd_cons = 0
            choices = np.random.choice(indices, self.num_stud)
            for choice in choices:
                rnd_cons += l_cons[choice]
            cons.append(rnd_cons)
        # Use median instead of mean in case of tailed distribution?
        return np.mean(cons), np.std(cons)

    def get_random_device_consumption(
        self, time, device_list, dev_stat, sampling="simple", device_random_length=100
    ):
        cons = []
        d_cons = []
        for d in device_list:
            d_cons.append(d.get_consumption(time))

        kernel = stats.gaussian_kde(dev_stat)
        if sampling == "simple":
            for i in range(device_random_length):
                rnd_cons = 0
                choices = np.rint(kernel.resample(self.num_stud)[0]) % len(d_cons)
                for choice in choices:
                    rnd_cons += d_cons[int(choice)]
                cons.append(rnd_cons)
        elif sampling == "mcmc":
            if emcee is None:
                raise ImportError("Emcee not imported")

            def log_prob(x):
                return kernel.logpdf(x)

            ndim, nwalkers = 1, self.num_stud
            p0 = np.random.randn(nwalkers, ndim)

            sampler = emcee.EnsembleSampler(nwalkers, ndim, log_prob)
            sampler.run_mcmc(p0, 1000)
            samples = np.rint(sampler.get_chain(flat=True)[:, 0]) % len(d_cons)
            for i in range(device_random_length):
                random_samples = np.random.choice(
                    np.arange(len(samples)), self.num_stud
                )
                choices = samples[random_samples]
                rnd_cons = 0
                for choice in choices:
                    rnd_cons += d_cons[int(choice)]
                cons.append(rnd_cons)
        return np.mean(cons), np.std(cons)

    def get_random_transportation_consumption(
        self,
        transport_list,
        mot,
        t_dur,
        lec_pd,
        sampling="simple",
        transport_random_length=100,
        debug=False,
    ):
        cons = []

        kernel = stats.gaussian_kde(np.vstack([mot, t_dur]))

        if sampling == "simple":
            for i in range(transport_random_length):
                rnd_cons = 0
                choices, duration = kernel.resample(self.num_stud)
                choices = np.rint(choices) % len(transport_list)
                for j, choice in enumerate(choices):
                    rnd_cons += (
                        transport_list[int(choice)].get_consumption(duration[j])
                        * 2
                        / lec_pd
                    )
                cons.append(rnd_cons)
        elif sampling == "mcmc":
            if emcee is None:
                raise ImportError("Emcee not imported")

            def log_prob(x):
                return kernel.logpdf(x)

            ndim, nwalkers = 2, self.num_stud
            p0 = np.random.randn(nwalkers, ndim)

            sampler = emcee.EnsembleSampler(nwalkers, ndim, log_prob)
            sampler.run_mcmc(p0, 1000)
            samples = sampler.get_chain(flat=True)
            for i in range(transport_random_length):
                random_samples = np.random.choice(
                    np.arange(len(samples[:, 0])), self.num_stud
                )
                choices, duration = samples[random_samples].T
                choices = np.rint(choices) % len(transport_list)
                rnd_cons = 0
                for j, choice in enumerate(choices):
                    rnd_cons += (
                        transport_list[int(choice)].get_consumption(duration[j])
                        * 2
                        / lec_pd
                    )
                cons.append(rnd_cons)

            if debug:
                try:
                    import corner

                    fig = corner.corner(
                        samples,
                        labels=["MoT", "Duration (min)"],
                    )
                    imgdata = io.StringIO()
                    fig.savefig(
                        imgdata,
                        format="svg",
                        bbox_inches="tight",
                        dpi=600,
                    )
                    imgdata.seek(0)

                    data = imgdata.getvalue()
                    self.debug_figures["transport"] = data

                except ImportError:
                    warnings.warn("Corner module not found")

        return np.mean(cons), np.std(cons)

    def get_consumption(
        self,
        time,
        mode,
        sampling="simple",
        living_random_length=100,
        device_random_length=100,
        transport_random_length=100,
        hybrid_grid=20,
    ):
        """
        Basic function to get the consumption of a lecture

        Parameters
        ----------
        time : float
            Duration of the lecture (min)
        mode : str
            Determines mode of lecture. Recognised modes:
            offline, online-streaming, online-vod,
            hybrid-streaming, hybrid-vod.
        sampling : str
            Method for samling. Either 'simple' or 'mcmc'.
        living_random_length : int
            Number of randomised draws for the living situation
        device_random_length : int
            Number of randomised draws for the devices
        transport_random_length : int
            Number of randomised draws for the transportation
        hybrid_grid : int
            Number of grid points on which hybrid fractions are calculated


        Returns
        -------
        consumption : float
            Consumption of lecture in kW
        stat_uncertainty : float
            Statistical uncertainty from sampling procedure in kWh

        """

        # Check if lecture format is specified correctly
        if mode not in [
            "online-streaming",
            "online-vod",
            "offline",
            "hybrid-streaming",
            "hybrid-vod",
        ]:
            raise ValueError("Specified lecture format not recognized")

        # Check if emcee could be imported if sampling is set to mcmc
        if sampling not in ["simple", "mcmc"]:
            raise ValueError("Specified sampling mode not recognized")
        if sampling == "mcmc" and emcee is None:
            raise ImportError(
                "Sampling is set to mcmc, but emcee could not be imported"
            )
        if self.num_stud < 10 and sampling == "mcmc":
            sampling = "simple"

        if mode == "online-streaming" or mode == "online-vod":
            # Calculation of the consumption for an online lecture
            # TODO Make sure that the calculation makes sense

            # Streaming service
            if mode == "online-streaming":
                if self.streaming is None:
                    # TODO Redirect to proper error page
                    raise AttributeError("Streaming service not set")
                c = self.streaming.get_consumption(time) * self.num_stud
                self.contribs["Streaming"].append(c)
                self.contribs_std["Streaming"].append(0)
                consumption = c
            elif mode == "online-vod":
                if self.vod is None:
                    # TODO Redirect to proper error page
                    raise AttributeError("VoD service not set")
                c = self.vod.get_consumption(time) * self.num_stud
                self.contribs["VoD"].append(c)
                self.contribs_std["VoD"].append(0)
                consumption = c
            stat_uncertainty = 0

            # Living situation
            if self.living is None:
                # Get randomised living situations
                living_list = LivingSituation.objects.order_by("living_name")
                if "random_living" in self.options:
                    c, s = self.get_random_living_consumption(
                        time, living_list, living_random_length=living_random_length
                    )
                else:
                    c = 0
                    s = 0
                    for l in living_list:
                        c += l.get_consumption(time) * self.num_stud / len(living_list)
            else:
                c = self.living.get_consumption(time) * self.num_stud
                s = 0
            self.contribs["Living"].append(c)
            self.contribs_std["Living"].append(s)
            consumption += c
            stat_uncertainty += s**2

            # Electronic devices
            if self.device is None:
                # Get randomised devices
                device_list = ElectronicDevice.objects.order_by("device_name")
                if "random_device" in self.options:
                    dev_stat = np.arange(len(device_list))
                    c, s = self.get_random_device_consumption(
                        time,
                        device_list,
                        dev_stat,
                        sampling=sampling,
                        device_random_length=device_random_length,
                    )
                elif self.faculty is not None:
                    if self.faculty.elec_dev_type_file_online is not None:
                        dev_stat = self.faculty.get_device_type_statistics(online=True)
                        c, s = self.get_random_device_consumption(
                            time,
                            device_list,
                            dev_stat,
                            sampling=sampling,
                            device_random_length=device_random_length,
                        )
                    else:
                        dev = self.faculty.elec_dev_type_online
                        c = dev.get_consumption(time) * self.num_stud
                else:
                    raise AttributeError("Faculty must be selected")
            else:
                c = self.device.get_consumption(time) * self.num_stud
                s = 0
            self.contribs["Devices"].append(c)
            self.contribs_std["Devices"].append(s)
            consumption += c
            stat_uncertainty += s**2

            return consumption, np.sqrt(stat_uncertainty)

        if mode == "offline":
            consumption = 0
            stat_uncertainty = 0

            # Lecture Hall
            if "beamer" in self.options:
                beamer = True
            else:
                beamer = False

            if "debug" in self.options:
                debug = True
            else:
                debug = False

            c = self.hall.get_consumption(time, beamer=beamer)
            s = 0
            self.contribs["Lecture hall"].append(c)
            self.contribs_std["Lecture hall"].append(s)

            consumption += c
            stat_uncertainty += s

            # Transportation
            transport_list = Transportation.objects.filter(
                university=self.university
            ).order_by("transport_name")

            mot, t_dur = self.university.get_transport_statistics()
            lec_pd = self.faculty.get_lecture_statistics()
            c, s = self.get_random_transportation_consumption(
                transport_list,
                mot,
                t_dur,
                lec_pd=lec_pd,
                sampling=sampling,
                transport_random_length=transport_random_length,
                debug=debug,
            )

            self.contribs["Transportation"].append(c)
            self.contribs_std["Transportation"].append(s)
            consumption += c
            stat_uncertainty += s**2

            # Electronic devices
            num_stud_bak = self.num_stud
            self.num_stud = int(np.rint(num_stud_bak * self.faculty.elec_dev_use / 100))
            if self.num_stud == 0:
                c = 0.0
                s = 0.0
            elif self.device is None:
                # Get randomised devices
                device_list = ElectronicDevice.objects.order_by("device_name")
                if "random_device" in self.options:
                    dev_stat = np.arange(len(device_list))
                    c, s = self.get_random_device_consumption(
                        time,
                        device_list,
                        dev_stat,
                        sampling=sampling,
                        device_random_length=device_random_length,
                    )
                elif self.faculty is not None:
                    if self.faculty.elec_dev_type_file_offline is not None:
                        dev_stat = self.faculty.get_device_type_statistics(online=False)
                        c, s = self.get_random_device_consumption(
                            time,
                            device_list,
                            dev_stat,
                            sampling=sampling,
                            device_random_length=device_random_length,
                        )
                    else:
                        dev = self.faculty.elec_dev_type_offline
                        c = dev.get_consumption(time) * self.num_stud
                else:
                    raise AttributeError("Faculty must be selected")
            else:
                c = self.device.get_consumption(time) * self.num_stud
                s = 0
            self.contribs["Devices"].append(c)
            self.contribs_std["Devices"].append(s)
            consumption += c
            stat_uncertainty += s**2

            self.num_stud = num_stud_bak

            return consumption, np.sqrt(stat_uncertainty)

        if mode == "hybrid-streaming" or mode == "hybrid-vod":

            if mode == "hybrid-streaming":
                aux_mode = "online-streaming"
            else:
                aux_mode = "online-vod"

            # Create student/ hyprid fraction grid
            if self.num_stud > hybrid_grid:
                grid = np.linspace(0, self.num_stud, hybrid_grid, dtype=int)
            else:
                grid = np.linspace(0, self.num_stud, self.num_stud, dtype=int)

            # Calculate hybrid consumption for each gridpoint
            num_stud_bak = self.num_stud

            cons = []
            cons_std = []
            for p in grid:
                if p == 0:
                    self.num_stud = num_stud_bak
                    c, s = self.get_consumption(
                        time,
                        "offline",
                        sampling=sampling,
                        living_random_length=living_random_length,
                        device_random_length=device_random_length,
                        transport_random_length=transport_random_length,
                        hybrid_grid=hybrid_grid,
                    )
                    cons.append(c)
                    cons_std.append(s)
                    if mode == "hybrid-streaming":
                        self.contribs["Streaming"].append(0.0)
                        self.contribs_std["Streaming"].append(0.0)
                    else:
                        self.contribs["VoD"].append(0.0)
                        self.contribs_std["VoD"].append(0.0)
                    self.contribs["Devices"].append(0.0)
                    self.contribs_std["Devices"].append(0.0)
                    self.contribs["Living"].append(0.0)
                    self.contribs_std["Living"].append(0.0)
                elif p == num_stud_bak:
                    self.contribs["Devices"].append(0.0)
                    self.contribs_std["Devices"].append(0.0)
                    self.num_stud = p
                    c, s = self.get_consumption(
                        time,
                        aux_mode,
                        sampling=sampling,
                        living_random_length=living_random_length,
                        device_random_length=device_random_length,
                        transport_random_length=transport_random_length,
                        hybrid_grid=hybrid_grid,
                    )
                    cons.append(c)
                    cons_std.append(s)
                    self.contribs["Lecture hall"].append(0.0)
                    self.contribs_std["Lecture hall"].append(0.0)
                    self.contribs["Transportation"].append(0.0)
                    self.contribs_std["Transportation"].append(0.0)
                else:
                    # Onsite contribution
                    self.num_stud = num_stud_bak - p
                    c_offline, s_offline = self.get_consumption(
                        time,
                        "offline",
                        sampling=sampling,
                        living_random_length=living_random_length,
                        device_random_length=device_random_length,
                        transport_random_length=transport_random_length,
                        hybrid_grid=hybrid_grid,
                    )

                    # Online Contribution
                    self.num_stud = p
                    c_online, s_online = self.get_consumption(
                        time,
                        aux_mode,
                        sampling=sampling,
                        living_random_length=living_random_length,
                        device_random_length=device_random_length,
                        transport_random_length=transport_random_length,
                        hybrid_grid=hybrid_grid,
                    )

                    cons.append(c_offline + c_online)
                    cons_std.append(np.sqrt(s_offline**2 + s_online**2))

            # Reset number of studenst
            self.num_stud = num_stud_bak

            # Find optimal hybrid fraction
            cons = np.array(cons)
            cons_std = np.array(cons_std)

            # Interpolate consumption values
            x = np.arange(self.num_stud + 1)
            func = interpolate.interp1d(grid, cons)
            func_std = interpolate.interp1d(grid, cons_std)

            cons = func(x)
            cons_std = func_std(x)

            min_ind = np.where(cons == min(cons))
            min_cons = cons[min_ind]
            min_std = cons_std[min_ind]

            self.contribs["Grid"] = grid.tolist()
            self.contribs_std["Grid"] = grid.tolist()
            self.figure = self.get_hybrid_figure(x, cons, cons_std, grid)

            return min_cons[0], min_std[0]

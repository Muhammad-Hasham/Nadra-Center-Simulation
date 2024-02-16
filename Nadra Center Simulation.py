import simpy
import random
import numpy as np
from tabulate import tabulate

NumEmployees = 10
Giving_fingerprint_signature_time = 5
submitting_required_docs_time = 7
Providing_correctDocs_time = 5
ProcessApplication_time = 7
ApproveIssuingOfCNIC_time = 4

ApplicantIntervalTime = 3
SimTime = 300
ApplicantsHandled = 0
priority_queue = []
regular_queue = []
is_priority_queue_active = False

results = []


class NadraCenter:

    def __init__(self, env, num_employees, giving_fingerprint_signature, submitting_required_docs,
                 providing_correct_docs, process_application, approve_issuing_of_cnic):
        self.env = env
        self.num_employees = simpy.Resource(env, num_employees)
        self.giving_fingerprint_signature = giving_fingerprint_signature
        self.submitting_required_docs = submitting_required_docs
        self.providing_correct_docs = providing_correct_docs
        self.process_application = process_application
        self.approve_issuing_of_cnic = approve_issuing_of_cnic

    def givingFingerprintSignature_act(self, customer):
        activity_time = max(2, np.random.normal(self.giving_fingerprint_signature, 1))
        yield self.env.timeout(activity_time)

    def submittingRequired_docs_act(self, customer):
        valid_docs = False
        while not valid_docs:
            activity_time = max(4, np.random.normal(self.submitting_required_docs, 2))
            yield self.env.timeout(activity_time)
            if random.random() < 0.5:
                valid_docs = True
        if valid_docs:
            service_time = max(7, np.random.normal(self.process_application, 2))
        else:
            service_time = max(5, np.random.normal(self.providing_correct_docs, 2))
            service_time += max(7, np.random.normal(self.process_application, 2))
        yield self.env.timeout(service_time)

    def providing_correct_docs_act(self, customer):
        activity_time = max(3, np.random.normal(self.providing_correct_docs, 2))
        yield self.env.timeout(activity_time)

    def process_application_act(self, customer):
        activity_time = max(5, np.random.normal(self.process_application, 2))
        yield self.env.timeout(activity_time)

    def approve_issuing_of_cnic_act(self, customer):
        activity_time = max(2, np.random.normal(self.approve_issuing_of_cnic, 2))
        yield self.env.timeout(activity_time)


def applicant(env, name, nadra_center, has_appointment):
    global ApplicantsHandled, priority_queue, regular_queue, is_priority_queue_active
    queue_type = "priority" if has_appointment else "regular"
    results.append([name, "Arrival Time", queue_type, env.now])
    if has_appointment:
        priority_queue.append(name)
    else:
        regular_queue.append(name)

    if len(priority_queue) > 0 and not is_priority_queue_active:
        is_priority_queue_active = True
        while len(priority_queue) > 0:
            customer_name = priority_queue.pop(0)
            service_time = 0

            yield env.process(nadra_center.givingFingerprintSignature_act(customer_name))
            service_time += max(2, np.random.normal(nadra_center.giving_fingerprint_signature, 1))
            results.append([customer_name, "Started FSA", "priority", env.now, service_time])

            yield env.process(nadra_center.submittingRequired_docs_act(customer_name))
            service_time += max(4, np.random.normal(nadra_center.submitting_required_docs, 2))
            results.append([customer_name, "Started SRDA", "priority", env.now, service_time])

            docs_valid = random.choice([True, False])
            if not docs_valid:
                yield env.process(nadra_center.providing_correct_docs_act(customer_name))
                service_time += max(Providing_correctDocs_time, np.random.normal(nadra_center.providing_correct_docs, 2)
                                    )
                results.append([customer_name, "Started PCDA", "priority", env.now, service_time])

            yield env.process(nadra_center.process_application_act(customer_name))
            service_time += max(ProcessApplication_time, np.random.normal(nadra_center.process_application, 2))
            results.append([customer_name, "Started PAA", "priority", env.now, service_time])

            service_time += max(ApproveIssuingOfCNIC_time, np.random.normal(ApproveIssuingOfCNIC_time, 2))
            results.append([customer_name, "Departure Time", queue_type, env.now, service_time])
            ApplicantsHandled += 1
        is_priority_queue_active = False

    else:
        if len(regular_queue) > 0:
            while len(regular_queue) > 0:
                customer_name = regular_queue.pop(0)
                service_time = 0

                yield env.process(nadra_center.givingFingerprintSignature_act(customer_name))
                service_time += max(2, np.random.normal(nadra_center.giving_fingerprint_signature, 1))
                results.append([customer_name, "Started FSA", "regular", env.now, service_time])

                yield env.process(nadra_center.submittingRequired_docs_act(customer_name))
                service_time += max(4, np.random.normal(nadra_center.submitting_required_docs, 2))
                results.append([customer_name, "Started SRDA", "regular", env.now, service_time])

                docs_valid = random.choice([True, False])
                if not docs_valid:
                    yield env.process(nadra_center.providing_correct_docs_act(customer_name))
                    service_time += max(Providing_correctDocs_time,
                                        np.random.normal(nadra_center.providing_correct_docs, 2)
                                        )
                    results.append([customer_name, "Started PCDA", "regular", env.now, service_time])

                yield env.process(nadra_center.process_application_act(customer_name))
                service_time += max(ProcessApplication_time, np.random.normal(nadra_center.process_application, 2))
                results.append([customer_name, "Started PAA", "regular", env.now, service_time])

                service_time += max(ApproveIssuingOfCNIC_time, np.random.normal(ApproveIssuingOfCNIC_time, 2))
                results.append([customer_name, "Departure Time", queue_type, env.now, service_time])
                ApplicantsHandled += 1


def setup(env, num_employees, applicant_interval, giving_fingerprints_sig, submitting_req_docs,
          providing_correct_docs, process_application, approve_issuing_of_cnic):
    nadra_center = NadraCenter(env, num_employees, giving_fingerprints_sig, submitting_req_docs,
                               providing_correct_docs, process_application, approve_issuing_of_cnic)

    for i in range(1, 2):
        env.process(applicant(env, i, nadra_center, False))

    while True:
        yield env.timeout(random.randint(applicant_interval - 1, applicant_interval + 1))
        i += 1
        has_appointment = random.choice([True, False])
        env.process(applicant(env, i, nadra_center, has_appointment))


print("Starting Nadra Center Simulation")
env = simpy.Environment()
env.process(setup(env, NumEmployees, ApplicantIntervalTime, Giving_fingerprint_signature_time,
                  submitting_required_docs_time, Providing_correctDocs_time, ProcessApplication_time,
                  ApproveIssuingOfCNIC_time))
env.run(until=SimTime)

print("Customers handled: " + str(ApplicantsHandled))
print(tabulate(results, headers=["Customer", "Action", "Queue", "Time", "Service Time"]))

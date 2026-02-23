Sample Questions for Midterm Exam
All,

I'm sharing a set of sample questions to help you prepare for the upcoming exam. A few important things to keep in mind:

These questions are meant to give you a sense of the format and style of questions you can expect — scenario-based questions that test your understanding of concepts, not memorization.
These specific questions will most likely not appear on the actual exam. Please do not over-rely on them or limit your studying to just these topics. The exam will cover the full breadth of material discussed in class.
Use these samples as a starting point to check your understanding, then make sure you're comfortable applying concepts across all the topics we've covered.
Good luck with your preparation!

Regards,

--Tejas



Question 1 – TCP vs UDP

Sarah is building two applications: a banking portal where every transaction must be reliably delivered, and a live sports score ticker where speed matters more than perfection. She's choosing between TCP and UDP for each.

Explain the key differences between TCP and UDP that would help Sarah make her decision. Which protocol should she choose for each application, and why

Question 2 – DNS TTL

Priya's company is planning a migration where their main website www.example.com will move from an old server (IP: 10.0.0.5) to a new server (IP: 10.0.0.99) over the weekend. She's worried that even after updating the DNS record, some users will still be directed to the old server for hours.

Explain what the TTL setting on a DNS record is and how it contributes to this problem. What would you advise Priya to do before the migration weekend to minimize downtime?

Question 3 – Horizontal vs Vertical Scaling

An e-commerce company experiences a 10x traffic spike every year during Black Friday. Their current setup runs on a single powerful server. The CTO is debating two strategies: upgrading to an even more powerful server, or distributing the load across multiple smaller servers.

Explain the difference between these two approaches — vertical and horizontal scaling. Discuss the trade-offs of each, and recommend which strategy is better suited for handling unpredictable traffic spikes like Black Friday.

Question 4 – Five Essential Characteristics of Cloud

Your manager claims that because the company recently moved its application to a set of virtual machines hosted in a co-location data center, they are now "in the cloud." You're not so sure.

According to NIST, what are the five essential characteristics an IT environment must exhibit to be considered cloud computing? Based on these characteristics, explain whether your manager's claim is justified or not.

Question 5 – Instance Store vs EBS-backed EC2

A data analytics team runs nightly batch jobs that process terabytes of raw log files. The jobs are compute-intensive, generate massive amounts of temporary intermediate data, and the results are written to S3 when complete. If a job fails, it simply restarts from scratch — no intermediate data needs to be preserved.

Explain the difference between an Instance Store-backed EC2 instance and an EBS-backed EC2 instance. Given the analytics team's workload described above, which backing store would you recommend and why? What is the key risk the team should be aware of with your recommendation?
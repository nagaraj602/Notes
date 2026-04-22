# AWS

---

## On-premise infrastructure

### Advantage:
- We have complete control of resources.
- Complete control of service and data
- It will have good application performance, since resources are provided in hardware, so latency is less and everything will work faster.

### Disadvantage of on-premise infrastructure:
- Costs: Organization need to bare both : capex and opex  
  - opex: electricity costs, licence of software and OS.  
  - Capex: server, network and physical components changes.

- Scaling limited: Means, we cannot scale the resources as we need, because we need to order resources, wait for delivery and setup and configuration of security which takes a minimum 4-5 months and by this time, the application needs might have moved to another resource itself.

- Low reliability and availability: If any failure happens in hardware or software components, we need to take care of our own and there are chances of data loss.

- Low fault tolerance: Ability to handle disaster is low like earthquake or any environmental issues happens then hardware will be affected and application goes down.

- Business downs: If business goes down then all the resources which are with you will be of no use, even if you recover opex, but you may not get capex as you don’t know if you get the same price while selling the resources.

- Human resource: Human resource is needed to maintain and setup everything and install all configurations which need technical professionals. Also security personnel were needed.

---

## Advantage of cloud infrastructure:
- Cost is reduced as everything is managed by cloud providers.
- We can scale resources as much as we can, as resources are provided on-demand and there will be no such delay and it will be done within a day.
- Availability: cloud providers offers 99.9% availability of server, which eliminates reliability and availability.
- Also fault tolerance is good and they have dedicated personnel to look after it.
- Resource pooling: we can pool our resource with cloud providers (VA).
- Measured service: We can pay for the service we used (pay as you go)
- Good agility: How fast we can build application. If we can build applications fast, then we can say it has high agility.

---

## Disadvantage of cloud computing:

1. Cost uncertainty: Cloud uses pay-as-you-go, which can become expensive if not managed properly.  
   Ex: Unused EC2 instance or any other services, or high data transfer, which leads to unexpected bills. No fee for data transfer in, but AWS charges for data transfer out.

2. Internet Dependency: Cloud services require a reliable internet connection.  
   Impact: No internet = No access to application/data.

3. Security & Privacy risks: Data is stored on third-party infrastructure.  
   Risks: Data breaches  
   - Misconfigurations (common issue in real projects)

4. Limited control: You don’t have full control over hardware & infrastructure.  
   Ex: Cannot access physical servers or customize deeply.

5. Vendor lock-in: Switching between providers is difficult.  
   Ex: Moving from AWS to another cloud requires redesign and migration effort.

6. Downtime and Outage: Even major cloud providers can have outages.  
   Impact: Applications may become unavailable temporarily.

7. Compliance challenges: Certain industries require strict data location and security rules.  
   Ex: Data must stay within a specific country.

8. Performance variability: Shared infrastructure can sometime cause inconsistent performance.

---

## Deployment model / Different types of cloud:

- Public cloud: If the resources are given to the users, we can use it by creating account in it. Ex: AWS, Azure, GCP.

- Private cloud: resources which are given to particular companies.  
  Ex: NASA, China, US military. Dell cloud, HP Cloud are private cloud who use it for their own use.

- Hybrid cloud: AWS, rackplace. It provides some service to the public and some are private. ex: App in AWS & sensitive data is in on-premise (private cloud)

- Community / multi cloud: If the cloud resource is available to a particular community then it is called as community cloud. If the resources are made available in multiple platforms, then we call it multi cloud. Ex: App in AWS & database is in GCP, so multiple providers is used.

---

## Service model / different cloud computing model:

- IAAS - (Infrastructure as a service): Provider provides virtualized hardware resources and user is responsible for managing operating system, application and data  
  Ex: AWS EC2

- PAAS: Platform as a service: Where platform is provided for application and we need to deploy application inside it. We deploy code & we don’t manage server or OS resources.  
  Ex: Google app engine.

- SAAS: (Software as a service): You get the application with all the resources is managed by provider, you just use the software.  
  Ex: S3, Gmail, IAM, cloudwatch, cloudtrail

- FAAS: Function as a service: Run a code without managing servers (serverless). You control only function code.  
  Ex: AWS Lambda

- CAAS: Container as a service: You just manage and run containers. You control :- containers and application.  
  Ex: AWS ECS/EKS, Kubernetes

---

## Easy comparisons

| Model | You manage | Example |
|------|-----------|--------|
| Iaas | OS + Apps | EC2 |
| Paas | Code only | Google App Engine |
| Saas | Nothing | Gmail |
| Faas | Functions | Lambda |
| Caas | Containers | Kubernetes, EKS |

---

## AWS Pricing:

- Computing: All the resources like RAM, EC2 instance, OS etc.  
  Linux and windows are billed on per second (1 sec) basis whereas MAC OS is billed on hourly basis (even if it is 30 minutes, you’ll be charged for 1 hour) as mac OS needs separate hardware resource from Apple. So for getting macOS instance, you need dedicated host. By default free account will not have dedicated servers. You need raise support ticket and get approval & then allocated.

- Storage: Pay for the data you store.

- Data transfer: Data transfer in is always free, data transfer out is chargeable.

---

## AWS global infrastructure:

- Regions: Location where resources are located or cluster of data center.  
  Go to AWS account top right → Account → AWS regions → Enable regions which are needed.

- Availability zone (AZs): Availability zones are isolated locations within a region, each with its own independent physical infrastructure, designed to be isolated from failures in other availability zones.

Region (Mumbai):

        |_ AZ-1
        |_ AZ-2
        |_ AZ-3


- Edge location / point of location: Is a small setup helps in caching of the data. It is located at the end user and many edge locations are present.  
  Ex: cloudflare, cloudfront.

- Edge cache: is the frequently accessed data stored inside edge location with higher bandwidth compared to edge location.

- Local zones: These zones offer very low latency which is ms. Even Netflix uses a local zone.

---

### Key features of an edge location:

1. Proximity: Edge locations are closer to users, reducing latency and improving performance.
2. Caching: Edge locations cache content, reducing the need for repeated requests to origin servers.
3. Content delivery: Edge locations deliver content directly to users, bypassing origin servers.
4. Security: Edge locations provide security features like SSL encryption and DDoS protection.
5. Low latency: Edge locations reduce latency, improving user experience and real-time applications.
6. High availability: Edge locations ensure high availability and redundancy, minimizing downtime.
7. Scalability: Edge locations can handle large volumes of traffic and scale with demand.
8. Real-time analytics: Edge locations provide real-time analytics and insights into user behavior.
9. Content optimization: Edge locations optimize content for different devices and networks.
10. Integration: Edge locations integrate with other cloud services and CDNs for a comprehensive solution.


---

## IAM: Identity and access management

IAM has two parts: Authentication and authorization.

- Authentication: is when we verify identity, the identity if the user belongs to AWS or not.  
- Authorization: what are the permission the identities have to perform specific tasks.

IAM is a global service and managed by AWS.

---

## Factors to be considered while choosing aws region to deploy any application:

1. Compliance: Rules & regulations set by the government in that region. example data of that region should be kept in that region itself, cannot store the application data in other region. Ex: Indian users data should be kept in India by having server in India itself.

2. Proximity: Proximity to users: Choose a region closest to your end users to reduce response time. If the region is far from end user then latency increases & application loads slow. If region is near to end user then latency decreases & application loads faster.  

   Latency means: The time taken for a request to travel from client to server and back (network delay).  
   Response time: The total time from sending a request to getting full response. It includes: latency (network delay), server processing time, data transfer time.

3. Available service: Not all AWS services are available in every region.  
   Ex: In hyderabad region, we cannot get Mac instance as aws has not added mac chips. Only few other regions have it.

4. AWS pricing: AWS pricing varies by region. Example: Some regions are cheaper for compute/storage than others, which impacts overall cost.

5. High Availability and Disaster Recovery: Check how many Availability zones (AZs) are in the region.  
   Ex: More AZs → better fault tolerance.

---

## In AWS, we categorized services into two type:

### Global services:
IAM, S3 (even though data is stored is region specific but buckets are unique, so it can be accessed from any region), Route 53, Cloudfront, AWS organization, WAF (web application firewall), Billing and cost managment, support center.

### Regional services:
EC2, VPC, RDS etc.

---

## AWS organization:

It is a service of AWS that helps you centrally manage multiple AWS accounts. It is mainly used by companies to organize, control and govern their cloud resources at scale.

- It tracks cost centrally & combines billing for all accounts into one invoice. Helps in volume discounts.
- It can apply policies to all accounts centrally/applied at organization level.  
  Ex: S3 policies, Resource control policies (RCPs), Service control policies (SCPs) etc.

Example for AWS organization: In some companies, they keep separate account for dev and testing and another account for production. So that security of production account resource are not compromised. Then these accounts are added in AWS organization to manage centrally.

Go to AWS account profile at the right top → Organization.

---

## Service quotas:

Here it has list of all the quotas for all the AWS resources. That means, it lists limitation of the services.  
Ex: AWS EC2 Auto scaling group per region is 500.

Go to AWS account top right → Service quota → select from dropdown → view quotas.

---

## AWS Account:

Here you’ll manage your account. It has option to change your full name, company name, address, phone number, website URL.

It shows Account ID as well as ARN number.

It also has option to add Alternate contacts, which can get notification about billing & other topics.

You can add three contacts:
1. Billing contact

# AWS Cloud (Amazon Web Services)

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
| Paas | Code only | AWS Elastic Beanstalk, Google App Engine |
| Saas | Nothing | S3, IAM, Cloudwatch, SNS, Route53, Gmail |
| Faas | Functions | Lambda |
| Caas | Containers | Kubernetes, AWS EKS |

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
2) operation contact  
3) Security contact  

For each of the above contact, you need to fill: Fullname, Title, Email address, Phone number.

The Account page also has option to enable & disable some additional region, that disabled by default. You cannot disable the default regions which are enabled by AWS at the creation of AWS account, such as united states (N. Virginia) etc.

Whenever you see any service as global service, those are hosted in N. Virginia.

You can also enable IAM user and role access to billing information.

---

## Billing and cost management:

### Home:
- It has cost summary, cost monitor, cost breakdown chart with last 6 months.
- Also it shows top trends in usage of any service in our account.
- It also has recommended actions section which shows some of the recommendation tips suggested by AWS.

### Bills:
- It shows all the billing details for current month.
- We can also check the bills of previous months.
- It shows breakdown of each service along with the region and with unit cost.
- You can also see the invoice & Tax invoice of previous month in the same page.
- It also shows the charges by Account.
- If you’re using organization account, then it shows the billing of each account in the Bills section.
- It do not only shows total billing per account, it has drop down for each account number, so that we can see breakdown of each service per each region.
- You can also down these bills using one click button.
- This is different from invoice. Invoice is generated only after payment is done, while you can download bills to get approval from your company.

### Payments:
- Here you will be adding billing address and payment information like credit card, Paypal or UPI and process the payment.

AWS won’t charge your account automatically. You need to manually process the payment. If payment is not done, then AWS will suspend the account.

You down all the invoice from Transaction section in the Payment page.

---

## Budgets:

If you want to set budget and if the cost exceeds the set threshold value, then we get alert via email and we can then act accordingly.

Go to Billing and cost management → Budgets → create budget → select suitable options like:
- zero spend budgets
- Monthly cost budgets
- Daily Savings Plans coverage budget
- Daily reservation Utilization budget

any name → Enter your budgeted amount → Email recipients: Add email addresses by separating with commas → Create budget.

Once budget is created, you can select that budget → Action → Edit  
→ you can set period:
- Daily
- Monthly
- Yearly
- Quarterly
- Custom

→ Budget renewal type:
- Recurring budget
- Expiring budget

→ Start month & year → Enter budget amount ($): 1 → Budget scope:
- All AWS service
- Filter specific AWS cost dimensions

→ Next → You can set threshold = 0.01

→ different alert type:
- email
- SNS (SMS to your phone)

→ Next → Review → save.

Here we can set budget as 1$ for free account and we can set threshold as 0.01, so that when free tier cross 0.01, it triggers alerts.

Budget: The total amount we have as amount. Ex: 100$  
Threshold: A minimum value to which alert should trigger, so that we can manage our service & optimize the service to keep cost below budget. We can set threshold $50.

---

## Pricing calculator:

We can select the services and get the estimate for your project based on each service with multiple regions.

You can choose each and every details.

Ex: In S3 bucket, you can choose regions, S3 class type, put, get threshold, amount of storage in GB, data transfer values etc.

---

## Security credentials:

Go to AWS account top-right corner → security credentials. This option is for AWS root account.

Here you can set password for your account or set MFA device for your account or you can set access key (which you can use for accessing AWS CLI).

### MFA: (Multi Factor authentication)
Already AWS have security layer like, user credential is passed during logging in. To add one more layer of security to the account, we use MFA. We get OTP to enter & then we can login to account.

We can set multiple MFA device:
- Passkey or security key
- Authenticator app
- Hardware TOTP tokens (generated from hardware TOTP which is generated from satellite)

### Setup:
Go to AWS account top right corner → Security credentials → MFA device → Device Name: <Any name> → MFA device:
- Passkey or security key
- Authenticator app
- Hardware TOTP Token

→ Next → Show QR code → Enter 2 codes → Add MFA device.

If MFA code is not working you can Resync the server in this page.

---

## Cloudshell:

You can see the option in AWS console at the top-right & bottom left with the symbol: >_

It is region specific service.

AWS cloudshell is browser-based terminal available directly inside the AWS management console.

### Key points:
- Runs in your browser (no setup needed)
- Comes pre-installed with AWS CLI, Git, python, etc.
- Automatically uses your login AWS credentials
- Temporary environments

It comes with 4GB RAM, 2 CPU, 16GB storage. Amazon linux OS.

---

## AWS support center:

If you want to get help related account related issue, billing related issue, service related issue, then we can go to support center & create a case and then get help.

You need to purchase support plan to get technical assistance.

There are 4 plans:
1) Basic support: Account related & billing related case. Free plan. Connected in 24 hour via email/web.  
2) Business support: Paid plan. You get assistance including technical assistance & connect with support in <30 minutes.  
3) Enterprise support: Paid plan. Same as Business support but connect with agent in <15 minutes.  
4) Unified operations: Paid plan: This is for mission critical workload. Connect with agent in 5 minutes.

---

## AWS console Home:

You can add widgets, so that you can see the shortcut for any of the option/tab you want to see.

imp: Add AWS Health, AWS blog post, Latest announcement.

---

## IAM:

IAM: Identity and access management: IAM has two parts: Authentication and authorization. IAM is used to control who can access what resources and what actions they can perform.

IAM is global service, hosted in N. Virginia & managed by AWS.

- IAM user: IAM user is an individual identity created in AWS for a specific person.
- IAM user group: IAM user group is a collection of IAM users where we can attach policies to the group which will be inherited by users.
- IAM Role: IAM Role is an identity with temporary permissions that can be assumed. No permanent credentials. Used by AWS service like EC2, Lambda, etc.

---

## IAM user creation:

Go to IAM → users → Create user → Enter username  
→ (here you can give console access, if not we can create user & then attach policy to it)  
→ provide user access to the AWS management console → I want to create an IAM user → Next  
→ Console password: set autogenerated password or select custom password  
→ (check or uncheck): users must create a new password at next sign-in  
→ next → Permissions options:

- Add user to group (If there is any existing group, then add user to it)
- Copy permissions (If there is any user with the exact permission, then select this)
- Attach policy directly (attaching policy listed in policy section)

→ I will select Attach policy directly → Here you have option to select policy from predefined policies or else you get option to create custom policy → I select predefined policy, S3 full access → Next → Create user →

It shows console URL, username & password. We can download these in CSV file.

---

## IAM password policy:

We can create our own password policy or follow the predefined password policy mentioned by AWS.

Go to IAM → Account settings → Password policy → Edit → custom  
→ select the ones which you want → save changes.

This is applied to all users.

---

## Resetting password for any user (password reset) OR Revoking AWS console access for any user:

If we want to revoke AWS console access for any user or if we want that user to change the password on next login,

Go to IAM: user → user name → Security credentials  
→ Manage console access → Disable console access → Revoke active console sessions → Disable access.

We can also reset password from the same above options.

Go to IAM user → user name → Security credentials → Manage console access → Reset password → Auto generated/custom  
→ user must create new password on next-sign-in → Reset password.

---

## Creating user groups:

Go to IAM → user groups → Create group →  
user group name: <Any name> → Add users to the group: If you have created user already, then you can select users, if not leave it as it is → Attach permissions policies: Here you can attach policies upto 10. You can select predefined policies or you can attach the policy created by you → Create user group.

If you go to permission section of group or each user, then you will see “type”, where it shows the type of policy attached.  
ex: AWS managed  
    Customer managed  

In the user section, if you click on any user, you see permission policies, there it show Attached via:
- Directly
- Group <group name>

---

## IAM Role (creation):

Gives permission for AWS service to access AWS resources.

Ex: Create Amazon linux ec2 & try connecting to S3.  
→ aws s3 ls  

o/p: Unable to locate credentials. You can configure credentials by running “aws configure”.

So create role to give access.

### Steps:
Go to IAM → Role → create role → select trusted policy:
- AWS service (Allow AWS services like EC2, Lambda, or others to perform actions in account)
- AWS account (Allow entities in other AWS accounts belonging to you or a 3rd party to perform actions in this account)
- Web identity (If you want to give access to mail accounts like gmail, microsoft then use this)
- SAML 2.0 federation (Integrating AD (Active directory), if you want to add AD & add some conditions, then you can do it here)
- Custom policy (If we want to create temp permission with time based then we can do here)

→ currently I will select as “AWS service”  
→ service on we case: EC2  
→ permission policies: S3fullaccess  
→ Next  
→ Role name: <Any name>

→ Create Role.

Now attach role to EC2 machine:  
Go to EC2 instance → select instance → Actions → security → Modify IAM Role → select the role from drop down → Update IAM role.

Now you can go ssh & try running the S3 listing command again.  
→ aws s3 ls  

Now it lists all the S3 bucket.

---

## Different ways of connecting to AWS:

There 3 different ways:
1) AWS console  
2) CLI access (AWS CLI)  
3) SDK  

1) You can login to AWS console with user credentials and MFA (if configured)

2) For CLI access, we need to install AWS CLI and configure the credential and then we can access AWS services and resources.  
What are all the permission you have in console, you also get it in AWS CLI.

3) SDK is used by developers to access AWS, SDK is programmatic way of accessing AWS. It can be written in python, java, .net  
This also needs access key to be generated from AWS user/Role section.

---

## AWS CLI:

(AWS command line interface access to AWS)

We can access AWS Services & AWS resources via CLI and manage them. This is useful during automation task.

### Installing AWS CLI:

You can go to AWS documentation for installation steps and there are 3 options:
- Linux
- mac OS
- windows

Linux: You can choose linux if you are using linux instance or else if you’re using git bash on your windows, then also this works. But you need to install unzip first.

macOS: Install aws cli in mac OS

windows: If you want to install aws CLI using windows command prompt.

After installing AWS CLI:  
```
aws --version
```

To interact with AWS resources, we need access key & this should be configured in AWS CLI device where it was installed, here username & password doesn’t work.

---

## Steps:

Go to AWS account → IAM → user → <user-name> → Security credentials → create access key → Command line interface (CLI)  
→ scroll down → Acknowledge → Next → Description tag name: Any name → create access key  

→ Now it show Access key ID & Secret access key → copy those → Done.

Now goto AWS CLI:  
```
aws configure
```

o/p: 
```
AWS Access key ID (None): paste Access key ID  
AWS secret access key (None): paste secret access key  
Default region name (None): us-east-1  
Default output format (None): json  
```

→ you can also choose “text” but json is best

```
aws s3 ls
```
Now you will be able to list S3 bucket

Ex: For this user I gave S3 & EC2 full access but no IAM access or any other access.

So if you try to list IAM user you get “You are not authorized”  
```
aws iam list-users
```

o/p: An error occurred (AccessDenied)

```
aws ec2 describe-instances
```
o/p: It shows the info of ec2 instance in json format

---

## AWS CLI config & credential path:

You can see the configuration settings & credentials which are stored in your machine AWS CLI in “.aws” directory.

It is located in home path of your machine.

```
cd .aws  
ls  
```
o/p: 

```
config   credentials
```
→ These are files, not folders

```
cat config
```

o/p:
```
[default]
region = ap-south-1
output = json

[profile user2]
region = ap-south-2
output = json
```

```
cat credentials
```

o/p:
```
[default]
aws_access_key_id = AKIAT121GHSERTDOB07
aws_secret_key = K8O+glue1pul9BNxdMKGwCCPJVFCG1c5w5xnNf1bwxe

[user2]
aws_access_key_id = AKIAT121GHSERTO5SPN5V6
aws_secret_key = -----
```


If you’re handing over your PC to another person or if you are returning your PC to IT team & getting new one, then you should delete these credentials, as this is stored plain text.

---

## Scenario:

In your organization, there will be multiple environment like dev, testing, production. So in each environment you will have different access key, so if we just use “aws configure” in our aws cli machine, it overlaps with the existing one & previous one will no longer available. To avoid that, we use profile in aws cli.

→ aws configure  

o/p:
```
AWS Access key ID [***********OB07]: paste access key ID  
AWS secret access key [************towx]: paste secret access key  
Default region name [ap-south-1]: us-east-1  
Default output format [json]: json  
```
So here, it is overwriting old credential with new one.

To avoid overwriting follow below step:

```
aws configure --profile ArtisanTek
```

o/p:
AWS Access key ID [None]: paste access key ID  
AWS secret access key [None]: paste secret access key  
Default region name [None]: ap-south-1  
Default output format [None]: json  

→ aws iam list-users --profile ArtisanTek  
o/p: It shows accessdenied as we didn’t give permission for this user.

Now, if you want to check the default user or the current user which is active for accessing any resource, use STS.

```
aws sts get-caller-identity
```

o/p:
```
{
"UserId": "AIDAT121GHSDFJXM7EFJ",
"Account": "225100968420",
"Arn": "arn:aws:iam::225100968420:user/ArtisanTek"
}
```

You can check aws-cli commands in aws documentation page.

---

## STS:

Security token service: is a service that provides temporary, limited-privilege credentials to access AWS resources.

STS lets you get temporary access instead of using permanent access keys.

### How it works:
1) You (user/service) request temporary credentials  
2) STS verify identities  
3) Returns:
   - Access key
   - Secret key
   - Session token  
4) These credentials expire after some time.

---

## Common STS API:

1) Assume Role: used to access another role (same or different account)
```
aws sts assume-role
--role-arn arn:aws:iam::123456789012:role/Admin
--role-session-name test
```


2) Get session Token: Temporary credentials for IAM user (with MFA)

3) Get caller identity: Shows who you are  
→ aws sts get-caller-identity

---

## Example use case:

You have:
- Account A (your account)
- Account B (Client account)

You:
- use STS + AssumeRole
- Access resources in Account B securely.

---

## Policy:

IAM policy is a Json document that defines permissions. It decides what actions are allowed or denied on which resources.

Simple definition:

IAM Policy = Rules of access
- Who → user / role / group
- What → Action (like read, write, delete)
- Which → Resource (S3 bucket, EC2, etc)

We can create policy using 2 options: Visual, JSON

---

## JSON:

Java script object notation.

Previously we used to have xml format, now we are using Json format.

In Json format, data is entered in Json format in the form of key & value pair with double quotes.

“key” = “value”

Key can only be in string format  
Value can be in any format like: string, number, arrays, boolean values

In Json format, it starts with flower bracket. { “key” = “value” }

Imp: Each line will end with comma, but not for last line.

---

## Example Policy:

Policy to give S3 access to an user.
```
{
"Version": "2012-10-17",
"ID": "S3 access to a user",
"Statement": {
"Sid": "1",
"Effect": "Allow",
"Action": "S3:",
"Principal": {
"AWS": "arn:aws:iam::123456789012:user/Artisan"
},
"Action": "S3:GetObject",
"Resource": "arn:aws:s3:::my-secure-bucket/",
"Condition": {
}
}
}
```

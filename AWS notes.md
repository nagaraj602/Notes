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

  IMP: Cannot attach multiple roles to instance. Only single role to instance.

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
        "IpAddress" : {
            "aws:SourceIp" : "192.168.1.0/24"
        }
    }
  }
}
```

#### Explanation:
• Version: Policy language version. Standard version in AWS is "2012-10-17"

• Statement: Policy can have multiple statements. Multiple statement is needed when we define policy for multiple service or resources.
If we are using single statement then { } square bracket is not needed. If we are writing multiple statement, then square bracket needed before flower bracket. Each statement one rule.
For single statement:
"Statement" : {
}

For multiple statements:
"Statement" : [
  {
  "sid":"1"
  }
  {
  "sid":"2"
  }
]

• Effect: "Effect" : "Allow"
Allow → grant permission
Deny → block permission

If we have created 2 statement for same service or resource & in statement, we have set effect as Allow & in another statement we have set it as Deny. Then AWS gives highest precedence to Deny.


• Principal: Defines who is allowed.
It can be:
• IAM user
• IAM Role
• AWS Account

If we use principal, then it used for that particular user or role only, it cannot be used for others.

Used only in resource-based policies (like S3 bucket policy)


• Action: Defines what action is allowed.
S3:GetObject = can read/download objects
cannot:
• upload
• Delete
• List bucket

• Resource: Defines which resource
"Resource" : "arn:aws:s3:::my-secure-bucket/*"

my-secure-bucket/* → all the objects inside bucket
Not the bucket itself

• This allows access to files, not bucket listing


• Condition: (security layer): Adds extra restriction
only allows access if request comes from IP, we can also add condition as only if MFA has done by user, then apply this policy.

"aws:SourceIp" : "192.168.1.0/24"

So it allows IP from 192.168.1.0 to 192.168.1.255


• Visual format option to create same policy:
Go to IAM → Policy → create policy → Select a service → EC2 → Actions
Allowed: You can select all EC2 Action (ec2:*) or select each action from dropdown → Resources: Here you can select all resources or select particular resource as instance. In instance also, you can select all instance or specify particular ARN of instance so that only that particular instance is given access. If you select different resource like key pair, subnet, VPC, security group, then you can give ARN or select as all. → conditions → Next → Policy name → Done.

The disadvantage of visual option to create Policy is that, you cannot select principals.

Ex: Simple policy to give S3 access to any user.

```
{
"Version": "2012-10-17",
"ID": "S3 access to a user",
"Statement": {
"Sid": "1",
"Effect": "Allow",
"Action": "s3:*",
"Resource": "*"
}
}
```

Above is for single statement.

For multi statement: It is useful for adding multiple resource or different permissions.

```
{
"Version": "2012-10-17",
"ID": "S3 access to a user",
"Statement": [
{
"Sid": "1",
"Effect": "Allow",
"Action": "s3:*",
"Resource": "*"
}
{
"Sid": "2",
"Effect": "Deny",
"Action": "s3:*",
"Resource": "*"
}
]
}
```

Here you have same resource but effect was set allow in 1st statement & Deny in 2nd statement. So AWS will take Deny as precedence.


## Policy structure/components of policy:
1. Version: The policy version “2012-10-17”, managed by AWS
2. Statement: A single policy statement which defines a specific permission or rule
3. Sid (Statement Id): A unique identifier for the statement
4. Effect: The effect of the statement, either “Allow” or “Deny”
5. Action: The specific AWS action(s) affected by the statement
6. Resource: The AWS resource(s) affected by the statement
7. Condition: Optional conditions that must be met for the statement to take effect
8. Principal: The AWS user, role or service that the policy is applied to


## Types of Policies:

### 1) Identity-based policy: Identity-based policies are permissions policies that are attached to IAM users, groups or roles, to define what actions those identities are allowed or denied to perform on AWS resources. These policies don’t include “Principal”.

    It has 3 types:
    a) AWS managed policies:
      • Created and maintained by AWS
      • Ready to use
      Ex: AmazonEC2ReadOnlyAccess
    
    b) Customer managed policies:
      • Created by the customer
      • Reusable across multiple identities
    
    c) Inline policy:
       This policy is directly attached to a single user, group or role. It cannot be reused for other identity. When identity gets deleted, policy gets deleted automatically.
       Use case: There are few policies attached to a group & we want to attach another policy to one user inside that group, then we can click on that user & create inline policy & attach the policy in it. Once you create inline policy, you will see “Attached via” as “Inline” in user details. Also when you go to IAM Policy section & if you try to search for that policy, you won’t see it in the list as it is not reusable.
    
    
    #### Steps to create inline policy:
      1) User: Go to IAM user → Click on user name → Permissions tab → Click on drop down of “Add permissions” → Create inline policy → You can do it using visual or using Json → Select service → Select Actions allowed → Select the resources → Request condition (if needed) → Next → Policy name → create policy.
      
      2) Groups: Go to IAM → user group → Click on group name → Permissions tab → Click on drop down of “Add permissions” → Create inline policy → Policy editor: visual/Json → Add service → Select actions → Select resource → Select request condition (if needed) → Next → Policy name → create policy.
      
      3) Role: Go to IAM → Role → Click on the role you created → Permissions tab → Click drop down “Add permissions” → create inline policy → Policy editor: visual or json → Select the service → Select actions → Select resources → Select request condition → Next → Policy name → create policy.


### 2) Resource based policy: These policies attached directly to AWS resources that define which principals (users, roles or accounts) are allowed or denied access to that resource and what actions they can perform.

  Ex: Allow IAM user “dev-user” to read S3 objects, only from a specific IP range.
  
  Steps: Login AWS → S3 → click your S3 bucket “my-secure-bucket” → goto permission tab → Bucket policy → Edit → Scroll down → Add new statement → you can either select actions, resources, conditions from side bar visual or write your own policy in Json format → Save changes.


### 3) Session based policy: Session policies are temporary permission limits applied when a role or user is assumed using STS, ensuring the session can only perform a restricted subset of allowed actions.
  
    Assume Role: Assume role allows a user or service temporarily use the permissions of an IAM role using short term credential (STS).
    
    You can assume role in console and also through CLI way. The access given in console will allow access via console only, you won’t get CLI access & vice versa.
    
    Console way: There are two methods:
    
    a) IAM → User → user name: test → ✓ Provide user access to the AWS management console → ✓ I want to create an IAM user.
    Console password: Autogenerated → uncheck “users must create a new password at next sign-in” → Next → Attach policy directly → You can either attach policy or leave it blank → scroll down → Next → Create user → Copy the credentials.
    
    Here you just created user, so that you can create role with STS and attach it to this user. This will become assume role. So this means access is given for temporary session. In this role you will add service, so that user can have permission to access that resource temporarily.
    
    • Role creation: IAM → Role → create role → custom trust policy →
    In the side bar → Read or write: AssumeRole → Add a principal →
    Add → Principal type → IAM users → ARN: paste ARN of the user you created → Add principal → Add permissions → select as “AmazonS3FullAccess” → Next → Role name: Any name → Create role.
    
    • Switching the role: You need to login to the user account you have created: After logging in, click on the “account” on the top-right side → It will hover → There you can see “Switch role”.
    
    • Go to S3 from that page → You can now access S3 bucket.
    
    • You can switch back from role by clicking on account → switch back or else, wait till session expires.
    
    • To modify the session timing, admin should update the session duration in IAM role.
    
    Go to IAM → Role → click on the role → Edit → Maximum session duration:
    • 1 hour
    • 2 hour
    • 4 hour
    • 8 hour
    • 12 hour
    • Custom duration
    
    → Save changes.
    
By default, assume role will have 1 hour.

b) Create user: Follow steps from previous method.

Create Role: IAM → Role → create role → AWS Account → This account → Next → Permission policy → "Amazon S3 Full Access" → Role name: Any name → create role.

Now add AssumeRole to the Role you have created: Go to IAM → Role → Click on the role you created → Trust relationship → Edit trust policy → From the side bar Action → Read or write → AssumeRole → Add a principal → Add → Principal type: IAM users → ARN: paste ARN of the user → Add principal → Update policy.

Now you can access the switch role. Follow instructions from previous method.

Note: If you’re are giving access for the user in different AWS account, you can add principal → another account → add ARN of it.


2) CLI way:

Create user: Follow the steps from previous method.

• Set up access key for the user: IAM → users → click on user name → Security credentials → Access key → AWS CLI access → Access key ID & Secret Access key is generated.

• Go to your server SSH terminal → AWS configure → set up AWS CLI.

• To check which CLI user profile is currently using, you can check using:
→ aws sts get-caller-identity

• Now if the user has no permission. So if we try to access S3, it will show access denied error.
→ aws s3 ls
o/p: error occurred, Access denied.

• Adding Assume Role: You have already created Assume role.

• Run this command to generate session based credentials.
→ aws sts assume-role --role-arn "arn-of-the-role" --role-session-name <session-name>


Ex:
→ aws sts assume-role --role-arn "arn:aws:iam::123456789:role/nag-role" --role-session-name nag-session

Now it show temporary access credentials.

Now you need to add it to bashrc so that CLI can use it. If you don’t do it, if you try to access S3, you get access denied error.

→ aws s3 ls
o/p: access denied

→ export AWS_ACCESS_KEY_ID=" "
→ export AWS_SECRET_ACCESS_KEY=" "
→ export AWS_SESSION_TOKEN=" "

Now run S3 listing:
→ aws s3 ls
o/p: Now you can list S3 bucket.


### Identity providers

Identity providers: IAM → Identity provider.

If you want add user with gmail, outlook or yahoo email users to the AWS account. Then you can use this.


### Access Analyzer

Access Analyzer: IAM → Access analyzer.

This will analyze the user permissions given to the user & gives report. If admin has given extra permission to the user & that permission is not really needed for that user. It shows unused permission. So that you can remove unused permission for the user.

It shows that this particular permission is not used in last 30 days. Then we can check it & remove it.


### Credential report

Credential report: IAM → credential report → Download credential report. You get .csv file which can be viewed in Excel sheet.

The credential report lists all your IAM users in this account and the status of their various credentials.

It includes, user name, password creation data, MFA enable status, last modified password date, last activity etc.


### Organization activity

Organization activity: It shows activities of different AWS account added in AWS organization.


### Permission boundary

Permission boundary: To restrict any user, group or role from having maximum permissions for them.

Ex: User has S3 access full. But in actual scenario, his role doesn’t need full access, He should be able to work with just S3 read access. Then we use permission boundary, we add only Read only access. Even though his main policy shows as S3 full access, when we set permission boundary, he can only read S3 bucket, cannot write or do any other operation.

IAM → user → <user-name> → Permissions → Scroll down → Permission boundary → set permission boundary → Select permission policy: "AmazonS3ReadOnlyAccess" → Set boundary.

It is same method for role & user group. If the user is in group, then go inside group → click the user → set permission boundary.


### Best practices to be followed in IAM, in order to keep aws account safe

Best practices to be followed in IAM, in order to keep aws account safe:

1) Avoid giving or using Root user access: Root has full unrestricted access. Use it only for billing & Account settings. Enable MFA for root & do not create access key for root.

2) Enable MFA everywhere: Enable MFA for all the users.

3) Use groups to manage permissions: Instead of assigning policies directly to users.

4) Use strong password policy: IAM → Account settings → Password policy. Rotate password reset every 90 days.

5) Provide Least privilege: Give only required permissions only.

6) Use Roles instead of long-term access keys: Avoid hard coding access keys in apps. Use IAM Roles + STS (temporary credentials)

This removes risk of key leakage.
Ex: EC2 → attach role
CI/CD → assume role.


7) Remove unused users, roles and permissions.

8) Enable auditing tools and monitoring tools: use AWS CloudTrail & cloudwatch.

9) Use permission boundaries.

10) Avoid inline policies when possible: Hard to manage & not reusable.

11) Use IAM Access Analyzer:
• Detects:
• Public access
• Cross account access

12) Use resource level permissions: "Resource": "*" → don’t use
ex: "Resource": "arn:aws:s3:::my-bucket/*"

13) Use condition policy: Allow only certain IP, Allow only the user having MFA.

"Condition": {
"IpAddress": {
"aws:SourceIp": "your_IP"
}
}


### IAM limitations

IAM limitations:
• 1000 users
• 5000 roles
• 100 policies per role.

• No built-in auditing: IAM doesn’t provide built in auditing capabilities, making it challenging to track and monitor access & change.

• Character limit: IAM policy document have character limits, which can make it difficult to write comprehensive policies. 6144 characters.


## SSM

SSM: AWS Systems manager: is a fully manage AWS service that enables you to centrally manage, configure, and operate your cloud and on-premises infrastructure using automation, secure IAM based access, without requiring direct network connectivity like SSH or RDP.

### SSM Parameter Store

SSM Parameter Store: It is a feature of SSM that lets you securely store, manage and retrieve configuration data & secret credentials.


You can store any Jenkins configuration files or any secret credentials in SSM parameter store.

[Jenkins configuration file is the jenkins dashboard config like: config.xml, jobs configs, plugin configs]

You can also store Jenkinsfile for pipeline but not recommended, use git for it.

Because we save the file in SSM as string & values, (not like typical upload file & store, it is like adding content to notepad).

Parameter store also allows versioning & Project Hierarchy.

• Versioning: You can store multiple version of same configuration file.

• Hierarchy: If you have 3 project, & if you want to store configuration of 3 project, storing them with string value is confusing. So we can use hierarchy, like

"project1/app/com/example/___"
"project2/app/com/example/___"


Parameter store is free service. So you can store till 8kb.


#### Steps

Steps:
Login to AWS → Systems manager → From the side bar → Scroll down → Parameter store → Create parameter store → Name: Any name (can be: /app/db-pass)
→ Tier: Standard - 4kb max → Standard
• Advanced - 8kb max
max store limit (free)

→ type:
• String (store any string, no commas)
• StringList (store multiple string with commas)
• SecureString (store any credentials (masked)) → Data type: text

Value: Paste the content. → Create parameter.

Explanation: when using string, you can give single value. StringList if you want to store any lists like usernames, then specify it with comma. Secure string: Here you can store encrypted credentials & you can either use default KMS or else use new KMS setup.


Once adding the value is done, you can edit it & it saves as version 2.

If you store credential, then value is encrypted & any other user who has only read access cannot view password, they can use name & SSM will fetch password to the application securely.

You can see versioning history & restore it by accessing that parameter history.

You can fetch the parameter values from AWS CLI:

You can use AWS CLI or use cloudshell.

• Go to cloudshell → Enter below command:

→ aws ssm get-parameters --names /app/db-passname
OR
→ aws ssm get-parameters --names <parameter-name>

o/p: This will show the value of /app/db-passname. This parameter is just name you added in it. So output will show all the details including, name: "/app/db-passname"
Type: String
Value:
Version: 1
LastModifiedDate:
ARN:
DataType: "text"

• If you used credential: (with encryption is shown, no direct value is shown)

→ aws ssm get-parameters --names /app/dbpassword

o/p: Now it shows encrypted password.

"Name": "/app/dbpassword",
"Type": "SecureString",
"Value": "AQICHMCM5LN90t......vg=",
"Version": "1",
"LastModifiedDate": "2026-07-30T03:31:18.343000+00:00",
"ARN": "arn:aws:ssm:ap-south-1:....../app/dbpassword",
"DataType": "text"


• If you want get the credential with decrypted value:
```
aws ssm get-parameters --names /app/dbpassword --with-decryption
```

o/p: It shows actual value.

"Name": "/app/dbpassword"
      .
      .
      .
"Value" : "nagala3"

To check the version history of parameter:
→ aws ssm get-parameter-history --name /app/dbuser

o/p: It shows all the versions along with values.

---

### SSM

SSM:

#### Advantage of SSM

Advantage of SSM:
1) Securely access servers (without SSH): It can connect to EC2 from browser or CLI. No SSH keys, no need to open port 22, no Bastion host needed. It is fully controlled using IAM. Session can be logged. If you lost SSH key, you can login with SSM without any key.

2) Run commands on Multiple servers: Execute commands across many instances at once. No login required. Ex: Install packages, Restart services.

3) Store & manage configs and secrets: We can use parameter store to store configuration files or secret credentials with versioning & hierarchy.

4) Automate operation tasks: Create workflow for repetitive tasks.
Ex: Create AMIs, stop/start instances, Patch systems.

5) Patch management: Patch manager → Automatically update OS packages, maintain compliance.

6) Monitor & manage infrastructure:
• Track instance status
• Collect inventory (OS, software installed)

---

### SSM requirement

SSM requirement:
1) SSM agent installed & running
2) IAM Role attached to the instance.
3) Network connectivity to SSM endpoints: Your instance must reach AWS SSM service.

option A: Internet Access:
• Public subnet + Internet gateway
• Private subnet + NAT Gateway

option B: VPC Endpoints:
• Create endpoints for:
  • SSM
  • ec2messages
  • ssmmessages
✓ No internet required
✓ More secure

4) Instance must be in "managed" state.

---

Check in: System manager → Managed instances  
→ If not listed agent/IAM/network issue.

5) Correct OS support:
• Linux/windows supported
• Custom AMIs must have SSM agent installed.

---

### Setting up SSM

Setting up SSM:
Go to IAM → Role → (create role → Add AWS service → service: EC2 → use case: EC2 Role for AWS system manager → Next → Role Name: Any name → create role.

Launch EC2 instance which has ssm installed already.

Login to AWS → EC2 → Launch instance → Amazon Linux → t2.micro  
→ Key pair name: Proceed without a key pair → Network settings → Create security group → Don’t allow any port → Scroll down → Advanced details → IAM instance profile → Select the role you have created for SSM access → Launch instance.

Wait for some time & then click on the instance you have created → Connect → Under the tab: "SSM Session Manager" → connect.

You’ll be able to access the server without any SSH connection.

If default shell shows as "sh" then switch to "bash" by typing "bash" on the terminal.

If you check the user of this, it shows as ssm-user  
→ whoami  
o/p: ssm-user

---

### Fleet manager

Fleet manager:
If there is only instance, then we manage it ourself.  
If there are multiple instance, then it is called fleet.  
To manage multiple instance, we have fleet manager.

It shows all the info of all the instances connected to the SSM like AMI ID, SSM agent name, status of instance, OS type, creation date.

#### Inventory

Inventory:
It tracks the packages installed on the machine.  
It track all the packages or softwares or OS version on the machine.

#### Patch manager

Patch manager:
If we want to update instance softwares or OS, then we can update all the instances at one go from here.

---

#### Run command

Run command:
If we want to run any command on multiple instances, then we can run it. We can either use the predefined command document or we can write on our own. We can choose instance manually or use tags, so that command will run on the specified instance. You can also schedule the command & choose safety controls.

#### Session manager

Session manager:
Click on start session → Target instance → Start session.

From here you can start ssm session and login to instance.

#### State manager

State manager:
Here you can manage the status of instance. If it is shutdown or not running, we can check here.

#### Automation

Automation:
we can write automation script & run those automation with scheduling.

#### Installing SSM agent on RHEL

Installing SSM agent on RHEL:
Go to AWS documentation & run the commands.  
Then it start showing up in fleet manager.

If you want run command from Run command section:
Go to SSM → Run command → Run a command → Select "AWS-RunShell Script" → Document version: 1 → Command parameter:

```bash
#!/bin/bash
sudo yum update -y
sudo dnf install nginx -y
```

→ working directory: keep it blank → Execution timeout: 3600

Target selection:
• specify instance tags → you need to tag instance in launch time  
• choose instance manually → you can select instance from dropdown  
• choose resource group → you can select any resource group  

→ Then add Tag key & Tag value here.  
Tags are good when instances are bulk → manual instance selection is difficult when we bulk instance.

→ You can set cloud watch alarm →

---

Set up SNS notification if need → Run.  
It shows as "in progress". Once command executed, it show success.

---

## Monitoring Tools

Monitoring Tools:
1) Cloud watch   2) Cloud Trail

Monitoring Tools helps in:
1) Efficient use of resources (Metrics)
2) Increasing performance (logs)

Alternative monitoring tools available in market which monitors both on-premise & cloud resources as well as application:
1) Dynatrace
2) Datadog
3) Splunk

Cloudwatch is used for monitoring resources & application inside the resources.

CloudTrail is used for activities management. It tracks all the activities we perform on any service or resources.

### Cloudwatch

Cloudwatch:
A centralized service that gives you real-time visibility into your infrastructure and applications by collecting metrics, logs, and events and turning them into actionable insights like alerts, dashboards, automation.

### Components of Cloudwatch

Components of Cloudwatch:

#### Metrics

1) Metrics:
Metrics are time-based numerical data points generated by AWS resources or services.

Ex:
• CPU usage of EC2
• Memory usage (custom metric)
• Request count in API

#### Logs

2) Logs:
Logs are text-based records of events generated by applications or system.

Ex:
• Error logs from an app
• Access logs from a web server

#### Alarms

3) Alarms:
Alarms watch metrics and trigger notification or actions when conditions are met.

Alarm has two part:
• Send notification (SNS)
• Action (Ex: scale server)

#### Dashboards

4) Dashboards:
Dashboards show metrics & logs in graphs & widgets.  
Gives me a visual overview of everything.

---

#### Events/EventBridge Integration

5) Events/EventBridge Integration:
Cloudwatch can react to system changes/events.

Ex:
When an EC2 instances stops, trigger automation.

#### Log insights (Querying logs)

6) Log insights (Querying logs):
Allows you to search and analyze logs using queries.  
i.e find patterns and debug faster.

---

### Types of cloudwatch monitoring

Types of cloudwatch monitoring:
1) Basic monitoring
2) Detailed monitoring

#### Basic monitoring

1) Basic monitoring:
Basic monitoring collects metrics at a lower frequency.  
Minimum interval of 5 minutes.

Key points:
• Basic monitoring is enabled automatically by default  
• Data granularity: 5 minutes  
• No extra cost  
• Suitable for general monitoring like non-critical workloads, systems where real-time response is not required.

Ex:
• CPU usage updated every 5 minutes  
• Network traffic every 5 minutes

#### Detailed monitoring

2) Detailed monitoring:
Detailed monitoring collects metrics at a higher frequency.  
Minimum interval of 1 minute.

Key points:
• You need to enable Detailed monitoring manually  
• Data granularity: 1 minute  
• Extra cost involved as Detailed monitoring is chargeable  
• Provides near real-time insights  

Good for:
• Production environment (critical system)  
• Auto scaling groups  
• Performance-sensitive application  

Ex:
• CPU spikes visible every minute  
• Faster alert triggering  

**Imp**: Even though datapoint shows for 1 minute, you can see the value for 10 seconds also. You can set it in the top-right.

### Data points

Data points: If we have set monitoring for 1 minute or 5 minute,
the point at each 1 minute/5minute, it shows the individual values of a
metric.

< data point >

10:00 10:01 10:02 10:03  → 10’o clock time

Definition: Data points are the individual values of a metric recorded
at a specific point in time or one measurement of a metric at a
specific time.
A data point = metric value + timestamp.

Each datapoints includes:
• Timestamp → when it was recorded
• Value → Metric value (e.g. CPU=70%)
• Unit → Percent, Bytes, Count, etc.
• Dimensions → Context (like instance ID).

Data points use:
• Accuracy: More data points = better understanding of behavior
• Faster Alerts: Alarms in cloudwatch evaluate based on data points.
  Ex: If CPU > 80% for 3 data points → trigger alarm
• Trend Analysis: Helps you see spikes, patterns, performance issues.

### Different AWS services and resources that can be integrated with Cloudwatch

Different AWS services and resources that can be integrated with
Cloudwatch:

1) Compute services:
• EC2 → CPU, disk, Network → metrics
• AWS Lambda → Invocations, errors, duration → logs
• Amazon ECS → Container metrics
• Amazon EKS → Cluster & pod monitoring
• AWS Elastic Beanstalk → app health

2) Storage service:
• Amazon S3 → request metrics, storage size
• Amazon EBS → IOPS, throughput

• Amazon EFS → throughput, connections

3) Database Services:
• Amazon RDS → CPU, connections, I/O
• Amazon Dynamo DB → read/write capacity
• Amazon Redshift → query performance

4) Networking & Content Delivery:
• Elastic Load balancing → request count, latency
• Amazon Cloudfront → cache hits, traffic
• Amazon VPC → flow logs.

5) Security & Identity:
• AWS CloudTrail → sends logs to Cloudwatch
• AWS IAM → activity via CloudTrail
• AWS WAF → security logs.

6) Application Integration Services:
• Amazon SNS → used with alarms
• Amazon SQS → queue depth metrics
• AWS step functions → Execution logs.

7) Devops & Management Tools:
• AWS Auto scaling → triggers based on Alarms
• AWS system manager → logs & automation
• AWS Cloudformation → stack events.

8) Monitoring & Observability Extension:
• AWS X-ray → request tracing
• Amazon managed Grafana → dashboard using Cloudwatch data.

### Cloudwatch integrates in 3 main ways

Cloudwatch integrates in 3 main ways:
1) Metrics: Services push performance numbers
   Ex: EC2 CPU, RDS connections
2) Logs: Applications and services send logs
   Ex: Lambda logs, VPC flow logs
3) Events: Triggers actions based on changes
   Ex: Instance stopped → Alert.

### Metrics

Metrics: In EC2 instance, when we select the instance → Monitoring

→ If you see the metrics, you’ll see few important one only. If want to
show all the metrics,
To see all the metrics, you can? Go to Cloudwatch →

Metrics → All metrics → You can select the service: EBS → EC2 → S3

→ By Image (AMI)
• Per Instance Metrics
• Aggregate instance type
• Across all instances

dimensions (Instance ID or Instance name) → You can search or select by
instance name or instance id → When you enter instance name/instance id
in search bar, it shows all the metrics name associated with
that instance → You can select metrics name based on requirement →
If you select multiple metrics, it adds up in the above graph section
(below metrics title name) → You can click on each metric name to
view it separately → From the top-right you can select the type of data view
(widget type)

• Line
• Datatable
• Stacked area
• Number
• Gauge
• Bar
• Pie

→ You can view the data of metrics → If you hover
on any metrics, it shows details info,
as well as option to set alarm.

Imp: By default, this shows metrics for 5 minutes.
To see for 1 minute, you need to enable Detailed monitoring on each instance.

### Dashboard

Dashboard: Dashboard shows metrics & logs in graphs & widgets.

Creating Dashboard: After selecting metrics by following previous
above steps → Actions → Add to Dashboard → Create new → Dashboard
name: Any name → widget type:
• Line → Number → Customize widget
• Data table
• Stacked area
• Number
• Gauge
• Bar
• Pie

title → You can change the name of each metric widget → Add to
Dashboard → Save.

After saving, you can rename Dashboard name,
• Auto layout Dashboard
• Settings
• Share
(Many other options)

### Share dashboard

Share dashboard: After creating Dashboard → Actions → Share Dashboard

→ You can share Dashboard in 3 ways:

1) Share your dashboard & require a username & password.
   Here you add any email address, they get temp link & they need
   to set their own username & password & then access dashboard.

2) Share your Dashboard Publicly:
   Click on start sharing → type “share” → confirm and preview policy →
   then also policy is attached → “Accept policy and generate sharable
   link” → Copy link.

3) Share all your account’s cloudwatch dashboards using single
   sign-on (SSO); For this you need to create userpool & add the
   SSO provider & then you can use it.

### Cloudwatch agents

Cloudwatch agents: Cloudwatch agents are software programs installed
on servers (EC2 or on-premises) to collect additional system-level
metrics and logs that cloudwatch does not capture by default.

In cloudwatch, by default it shows only few metrics for the
aws services, even if we enable detailed monitoring. That is because,
cloudwatch needs agents to be installed on EC2 to get the more
metrics like EBS metrics, CPU metrics etc.

Even though cloudwatch gets some default metrics by default,
But for getting logs (application log), it mandatorily needs cloudwatch
agents. Without agents, we don’t get logs.

In logs there are two things:
→ AWS managed logs → No agent needed. AWS will do it.
   Ex: VPC flowlogs, IAM logs
→ User managed logs → Here agent installation is must

### Alarms

Alarms: Single metric will have single alarm. We will set the
value. Once you setup alarm, alarm will keep on working
and gathers all the datapoints & if the datapoint crosses
threshold value, alarm will take the actions you have defined.

There are 3 type of Alarm states:

1) Insufficient_data State: There is not enough data to determine the
state.
when this happens:
• Alarm just created
• Metric not reporting (you set for 5 minutes so, there is no data till then)
• Instance stopped or no data points available.

2) OK State: The metric is within the defined threshold (normal condition)
Ex: CPU < 80%
• System is healthy
Meaning: Everything is fine, no action needed.

3) Alarm State: The metric has crossed the threshold.

Actions that can happen:
• Send notification via Amazon SNS
• Trigger scaling via AWS auto scaling
• Stop/terminate/recover an EC2 instance (AMI)

Ex: CPU > 80% for 3 consecutive data points
Meaning: Something is wrong → Trigger action.

Important concept Behind Alarm States:

1. Evaluation periods: Number of datapoints checked
   Ex: 3 periods of 1 minute each

2. Threshold: Limit you define
   Ex: CPU > 80%

3. Datapoints in Alarm: How many breaches trigger alarm
   Ex: 2 out of 3 datapoints must exceed threshold

Note: You can perform Actions on any state like OK, insufficient
data or Alarm state. There is no mandatory that

Action only applied for Alarm state.

Creating Alarm: Go to cloudwatch → Alarms → Create Alarm → Select
metric → Search for metric with your instance ID → Select metric
(You can select only single metric)

statistic:
• Average
• Sum
• Maximum
• Minimum
• Sample count
• IGM
• P90 (Percentage)
• tm 90
• tc 90
• ts 90
...

→ Static → Static → Whenever CPU utilization is:
• Greater
• Greater/equal
• Lower/equal
• Lower

→ Greater than: 70 → Additional configuration → Datapoints
to alarm:
1 out of 1 → Next → Alarm state trigger:
2 out of 5 (can be anything)

→ In alarm → OK
• Insufficient data

→ In-alarm → Send a notification to the following

SNS topic:
• Select an existing SNS topic → create new topic
• Create new topic
• Use topic ARN to notify other accounts

→ Topic name: by default AWS generate it or you can give any name of your wish

→ Email endpoints that will receive the notification: Add email addresses
with comma → Create topic → There are different actions: lambda
action → You can setup → Auto scaling Action: Add Auto scaling action → EC2 action : Alarm state trigger → Add EC2 action → Alarm state trigger:
• In alarm • OK • Insufficient data → In alarm → Take following action:

• Stop this instance → Stop this instance → Next → Alarm name:
• Terminate this instance
• Reboot this instance

Any name → Next → Review the settings → Create alarm.

By default, newly created, alarm will be in insufficient data state.

You can stress the CPU using:
→ sudo yum install stress -y
→ stress -c 1 -t 3600    OR → yes > /dev/null

cpu core → If 2 core, then stress -c 2 -t 3600

Now you start getting notification.

### Explanation

Explanation:

statistics: Statistic define how multiple data points within a time
period are aggregated into a single value before the alarm evaluates
them.

Why statistics are needed: Cloudwatch doesn’t evaluate every raw
data point individually. Instead it:
• Collects multiple data points in a time window (period)
• Applies statistic
• Uses the result to check the alarm condition.

• Data points to alarm: 1 out of 1, 2 out of 5, 5 out of 5, etc.

This setting controls how many data points must breach the threshold
before the alarm goes into ALARM state.

1 out of 1: If 1 data point breaches → ALARM
Behavior: Very sensitive.

2 out of 5: At least 2 out of 5 datapoints must breach.

we use when: You want to avoid false alarm.
Allow small fluctuation.


## SNS

SNS: Simple notification Service: A fully managed publish/subscribe
messaging service that enables applications, services and users to
send and receive notification instantly at scale.

Publisher sends a message to a topic (header/subject) SNS
topic will distribute the message to subscriber and subscriber
will receive it (email, SMS, Lambda, HTTP, SQS etc)

SNS lets you send one message & deliver it to many subscribers
(fan out model).

Key features:
• Scalable: handles millions of message
• Fully managed → No servers to maintain
• Fast delivery → near real-time
• Flexible → multiple subscriber types.

Steps: Go to SNS → Topics → Create Topic →

→ Type:
• FIFO (First In, First Out) → standard → Topic name
• Standard

• You can add the topic of the message (subject of message) → Display
name: You can add any name → create topic → Create subscription →

Protocol:
• Amazon Kinesis Data Firehouse
• Amazon SQS
• AWS Lambda
• Email
• Email-json
• HTTP
• HTTPS
• Platform application endpoint
• SMS

→ Email → Endpoint:

→ Email address with commas → Create subscription → Then subscriber
will receive email to confirm subscription, only then it is successful.


Once it is done, you can integrate it in AWS service or
application.

You can do SMS notification also. You need to select SMS in protocol
section while creating subscription.

## SQS

SQS: Simple Queue service: is a message queue used to
decouple systems (service/application send notification to SQS & then SQS to another
service/application). One service sends messages, another processes
them later.

### Types of SQS Queue

Types of SQS Queue:

1) Standard queue: Default and most commonly used. No ordering of
message.

Key features:
• At-least-once delivery → message may be delivered
  more than once.
• Best-effort ordering → order is not guaranteed.
• High throughput → virtually unlimited messages per
  second.
• Subscription protocols → SQS, Lambda, Data Firehouse,
  HTTP, HTTPS, SMS, email, mobile application endpoint.

2) FIFO: First In First Out: Strictly preserved message ordering.

Key features:
• Exactly-once processing (no duplicate)
• Strict ordering → messages processed in the exact
  order sent
• Lower throughput compared to standard.

use case: Financial transactions, order processing system,
any workflow where sequence is critical.


## EC2

EC2: Amazon Elastic compute cloud:

Elastic: The service can automatically scale capacity up or down based
on demand.

Compute: It provides virtual machines (CPU, RAM, Storage, network)
to run application.

Cloud: Resources are managed within Amazon’s global data centers.


### Instance

Instance: These are virtual servers that can be configured with
different operating system, memory and CPU capacity.

How AWS gives server is that they have huge physical server
like 100 CPU, 128GB RAM, 16TB storage. Then they use hypervisor
to divide it into smaller virtual machines. We can call it as guest
machines. Each VM can have their own OS, applications.

### There are 2 type of hypervisor

There are 2 type of hypervisor.

1) Type 1 hypervisor: These are created on physical server and create
VM in it. These are called bare metal hypervisor.

2) Type 2 hypervisor: These hypervisor installed on laptop, where we
install hypervisor on existing OS and use custom VMS.
Like on windows laptop, we use virtualbox & install
Linux OS or windows OS.
We can also consider container as Type 2 hypervisor.


EC2 host will have memory, CPU, storage, network. In storage there
are 2 types of storages that can be attached.

1) Ephemeral (Temporary storage): It’s attached as DAS (direct attached storage)

when we stop & start instance, the instance will not remain & even the storage
will no longer there. we get different instance with temporary storage.

This is chosen when speed matters more than durability.

Here also we attach EBS itself, but it’s temporary storage.

common real use:
• Caching layers (e.g Redis, temp cache)
• Big data processing (Hadoop, Spark intermediate
  processing)
• Batch jobs / ETL pipeline
• Temporary file processing (video encoding, image processing)
• High performance workloads needing ultra-low
  latency.

In these case, losing data is acceptable because:
• It can be recomputed
• or stored elsewhere permanently after processing.

when it is not used:
• If data is important
• Hard to recreate
• Needs backup

Then use:
• Amazon EBS (block storage)
• Amazon S3 (object storage)


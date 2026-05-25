# Orion Federal Analytics Agency Personas

All personas below are synthetic and fictional for demo use only.

## USR001 - Marcus Webb
Marcus Webb is the Identity Operations Lead for Orion Federal Analytics Agency. He joined on 2019-03-15 and supports Azure tenant administration plus AWS GovCloud administration for continuity scenarios. Marcus uses an authenticator app and is PIM-eligible for Global Administrator, but his AWS AdministratorAccess remains standing, so Claude should recognize that he is safer than peers yet still part of the highest-risk cross-cloud admin cohort.

## USR002 - Diana Reyes
Diana Reyes serves as Deputy Infrastructure Chief and joined the agency on 2021-07-22. She holds permanent Global Administrator rights in Azure and permanent AdministratorAccess in AWS GovCloud. Her only MFA method is SMS, which makes her the clearest example of a privileged account with weak authentication and direct mission impact if compromised.

## USR003 - Kevin Holbrook
Kevin Holbrook is the Privileged Access Engineer responsible for approval workflows and privileged access hygiene. Since 2020-01-10 he has held Privileged Role Administrator in Azure and AdministratorAccess eligibility in AWS, protected by hardware FIDO2 and approval-backed PIM. Claude should note that Kevin is comparatively mature but still creates concentration risk because he can bridge both clouds when activated.

## USR004 - Sandra Okafor
Sandra Okafor manages continuity of operations and received emergency global admin rights during a temporary incident 90 days ago. The temporary access was never removed, leaving her with Global Administrator in Azure and AdministratorAccess in AWS despite no longer needing that standing privilege. She uses an authenticator app, but the stale emergency elevation remains a critical governance failure.

## USR005 - Tyler Nguyen
Tyler Nguyen is a cloud platform engineer who joined on 2022-04-18. He retains permanent Privileged Role Administrator rights in Azure and AWS PowerUserAccess, even though his daily work focuses on automation support. His access profile demonstrates how standing privilege drifts into engineering teams when PIM conversion is not enforced.

## USR006 - Priya Malhotra
Priya Malhotra is a Security Administrator in the cyber defense team. She uses both an authenticator app and FIDO2 hardware, and her Azure Security Administrator role is PIM-eligible rather than always on. Priya still spans Azure and AWS security tooling, but her posture is one of the better-controlled examples in the dataset.

## USR007 - Jamal Carter
Jamal Carter is an application platform engineer supporting mission applications. He holds Azure Application Administrator and AWS PowerUserAccess, but relies only on SMS MFA. The narrative risk is not just phishing; compromise of Jamal could enable malicious app registration changes that disrupt mission workflows.

## USR008 - Leslie Morgan
Leslie Morgan administers GCC High messaging and collaboration services. Leslie uses an authenticator app and has Exchange Administrator in Azure plus AWS PowerUserAccess for supporting integrated notification pipelines. The account is moderately risky because privileged access is standing rather than just-in-time.

## USR009 - Anitha Krishnan
Anitha Krishnan is a senior data scientist focused on OSINT analytics pipelines. She has Azure ML Contributor plus AWS S3 and SageMaker access, which aligns with her role. Claude should treat her as a relatively standard cross-cloud data user rather than an administrator.

## USR010 - Derek Flynn
Derek Flynn is a data scientist who joined on 2022-06-11. His Azure Contributor and AWS S3/SageMaker access support model training and data labeling tasks. His profile is routine and mostly important as a baseline for comparing genuinely anomalous data scientists such as Tamara Osei.

## USR011 - Tamara Osei
Tamara Osei moved from the Cyber Operations team into the OSINT Analytics data science team six months ago. She should now only need Azure ML Contributor and AWS S3/SageMaker access, but she still retains Security Reader and Threat Intelligence Contributor from her previous role. This transferred-employee narrative is the key anomaly Claude should catch because it indicates stale access and overprivilege after an internal move.

## USR012 - Brandon Hill
Brandon Hill is a junior data scientist who joined on 2023-05-01. He uses hardware FIDO2 and holds only the expected Azure Contributor and AWS S3/SageMaker access required for analytics work. Brandon is included to show that strong MFA and scoped permissions are achievable even for new staff.

## USR013 - Fatima Al-Hassan
Fatima Al-Hassan works in the Mission AI Lab and experiments with AWS Bedrock for synthetic generative use cases. She still authenticates with SMS even though her Azure and AWS access provide broad dataset handling and model experimentation capability. Claude should recommend phishing-resistant MFA rollout for her before Bedrock use expands.

## USR014 - Clarence Stewart
Clarence Stewart is a data analyst with Azure Reader and AWS S3 read-only access. He uses an authenticator app and mainly supports reporting and quality checks. His account is low risk relative to the rest of the environment.

## USR015 - Nora Pacheco
Nora Pacheco is a mission analyst in the fusion cell with read-only access across both clouds. Her access profile aligns with least privilege and she uses an authenticator app. She helps demonstrate what normal analyst access should look like.

## USR016 - Omar Abdullah
Omar Abdullah is another mission analyst with routine Reader and ReadOnlyAccess assignments. He uses an authenticator app and has no notable risk indicators beyond the need for recurring access review cadence. Claude should not overstate risk for Omar.

## USR017 - Jenny Tran
Jenny Tran is a mission analyst with only read-only roles on paper, but she authenticates with email OTP and appears in audit logs using the svc-fusion-ingest service account. Investigators confirmed credential sharing between Jenny and SVC001. That means her effective blast radius is much larger than her nominal role set suggests, and it creates a direct compliance issue under IA-5 and AC-2.

## USR018 - Paulo Ferreira
Paulo Ferreira is a low-risk mission analyst using standard authenticator-app MFA. He has Reader access in Azure and ReadOnlyAccess in AWS for mission reporting. Paulo mainly serves as a control case within the user population.

## SVC001 - svc-fusion-ingest
svc-fusion-ingest is a service account used by the fusion ingest pipeline. It has Azure Storage Contributor plus expansive AWS S3, SQS, and Lambda rights, no MFA, and no designated owner. Audit evidence also shows it was last used by Jenny Tran, which means the account is both overscoped and entangled in confirmed credential sharing.

## SVC002 - svc-report-export
svc-report-export is a reporting export service account with Azure Blob Storage Contributor and AWS S3 PutObject access. Its technical permissions are more reasonable than SVC001, but its owner of record has departed the agency. Claude should call for owner reassignment and governance cleanup rather than panic-level remediation.

## CTR001 - Rafael Vega
Rafael Vega is a contractor whose engagement ended on 2024-12-31. Despite contract end, his Azure Reader and AWS ReadOnlyAccess remained active, and the account logged in on 2025-01-15 after the contract had expired. This is a textbook post-contract deprovisioning failure with compliance and insider-risk implications.

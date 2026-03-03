"""
download_papers.py
Downloads all found PDFs into a "papers" subfolder.
Run: python download_papers.py
"""

import requests, os

os.makedirs("papers", exist_ok=True)

papers = [
    ("https://arxiv.org/pdf/2210.02441v3", "papers/Ask_Me_Anything_A_simple_strategy_for_prompting_language_models.pdf"),
    ("https://arxiv.org/pdf/2210.03945v2", "papers/UNDERSTANDING_HTML_WITH_LARGE_LANGUAGE_MODELS.pdf"),
    ("https://arxiv.org/pdf/2210.01293v2", "papers/ThinkSum_Probabilistic_reasoning_over_sets_using_large_language_models.pdf"),
    ("https://arxiv.org/pdf/2206.12131v3", "papers/MVP_Multi-task_Supervised_Pre-training_for_Natural_Language_Generation.pdf"),
    ("https://arxiv.org/pdf/1909.03329v2", "papers/LAMOL_LAnguage_MOdeling_for_Lifelong_Language_Learning.pdf"),
    ("https://arxiv.org/pdf/2212.10711v1", "papers/Task_Ambiguity_in_Humans_and_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2109.07740v1", "papers/Scaling_Laws_for_Neural_Machine_Translation.pdf"),
    ("https://arxiv.org/pdf/2105.11447v1", "papers/True_Few-Shot_Learning_with_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2211.04205v2", "papers/Preserving_Semantics_in_Textual_Adversarial_Attacks.pdf"),
    ("https://arxiv.org/pdf/2209.15189v1", "papers/Learning_by_Distilling_Context.pdf"),
    ("https://arxiv.org/pdf/2209.14389v2", "papers/Downstream_Datasets_Make_Surprisingly_Good_Pretraining_Corpora.pdf"),
    ("https://arxiv.org/pdf/2207.05987v3", "papers/DocPrompting_Generating_Code_by_Retrieving_the_Docs.pdf"),
    ("https://arxiv.org/pdf/2012.14388v3", "papers/Universal_Sentence_Representations_Learning_with_Conditional_Masked_Language_Model.pdf"),
    ("https://arxiv.org/pdf/2105.05541v1", "papers/Evaluating_Gender_Bias_in_Natural_Language_Inference.pdf"),
    ("https://arxiv.org/pdf/2304.04358v1", "papers/WebBrain_Learning_to_Generate_Factually_Correct_Articles_for_Queries_by_Grounding_on_Large_Web_Corpu.pdf"),
    ("https://arxiv.org/pdf/2202.04538v2", "papers/Generating_Training_Data_with_Language_Models_Towards_Zero-Shot_Language_Understanding.pdf"),
    ("https://arxiv.org/pdf/2104.08410v1", "papers/Identifying_the_Limits_of_Cross-Domain_Knowledge_Transfer_for_Pretrained_Models.pdf"),
    ("https://aclanthology.org/2023.acl-long.658.pdf", "papers/Contrastive_Novelty_Learning_Anticipating_Outliers_with_Large_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2104.06960v2", "papers/K-PLUG_KNOWLEDGE-INJECTED_PRE-TRAINED_LANGUAGE_MODEL_FOR_NATURAL_LANGUAGE_UNDERSTANDING_AND_GENERATI.pdf"),
    ("https://arxiv.org/pdf/2212.06950v2", "papers/Pre-trained_Language_Models_can_be_Fully_Zero-Shot_Learners.pdf"),
    ("https://aclanthology.org/2021.repl4nlp-1.4.pdf", "papers/Representation_and_Bias_in_Multilingual_NLP_Insights_from_Controlled_Experiments_on_Conditional_Lang.pdf"),
    ("https://aclanthology.org/2023.findings-emnlp.1038.pdf", "papers/Closed_Boundary_Learning_for_NLP_Classification_Tasks_with_the_Universum_Class.pdf"),
    ("https://aclanthology.org/2025.babylm-main.1.pdf", "papers/Improving_Language_Model_Pretraining_with_Text_Structure_Information.pdf"),
    ("https://arxiv.org/pdf/2110.05448v1", "papers/Unsupervised_Neural_Machine_Translation_with_Generative_Language_Models_Only.pdf"),
    ("https://arxiv.org/pdf/2210.12353v3", "papers/Leveraging_Large_Language_Models_for_Multiple_Choice_Question_Answering.pdf"),
    ("https://arxiv.org/pdf/2107.11976v2", "papers/One_Question_Answering_Model_for_Many_Languages_with_Cross-lingual_Dense_Passage_Retrieval.pdf"),
    ("https://arxiv.org/pdf/2205.10036v1", "papers/Exploring_extreme_parameter_compression_for_pre-trained_language_models.pdf"),
    ("https://arxiv.org/pdf/2112.11668v1", "papers/How_Should_Pre-Trained_Language_Models_Be_Fine-Tuned_Towards_Adversarial_Robustness.pdf"),
    ("https://arxiv.org/pdf/2203.10378v1", "papers/On_Robust_Prefix-Tuning_for_Text_Classification.pdf"),
    ("https://aclanthology.org/2023.acl-long.128.pdf", "papers/Forgetful_causal_masking_makes_causal_language_models_better_zero-shot_learners.pdf"),
    ("https://arxiv.org/pdf/2110.07298v3", "papers/LFPT5_A_Unified_Framework_for_Lifelong_Few-shot_Language_Learning_Based_on_Prompt_Tuning_of_T5.pdf"),
    ("https://arxiv.org/pdf/2212.00196v2", "papers/Data-Efficient_Finetuning_Using_Cross-Task_Nearest_Neighbors.pdf"),
    ("https://arxiv.org/pdf/2202.02664v2", "papers/No_Parameters_Left_Behind_Sensitivity_Guided_Adaptive_Learning_Rate_for_Training_Large_Transformer_M.pdf"),
    ("https://www.preprints.org/frontend/manuscript/3dddd28c17737a55bfb33e767c50968c/download_pub", "papers/How_(Un)Fair_is_Text_Summarization.pdf"),
    ("https://arxiv.org/pdf/2211.09066v1", "papers/Teaching_Algorithmic_Reasoning_via_In-context_Learning.pdf"),
    ("https://arxiv.org/pdf/2110.04366v3", "papers/Towards_a_Unified_View_of_Parameter-Efficient_Transfer_Learning.pdf"),
    ("https://arxiv.org/pdf/2106.12672v3", "papers/Charformer_Fast_Character_Transformers_via_Gradient-based_Subword_Tokenization.pdf"),
    ("https://www.aclweb.org/anthology/2020.findings-emnlp.25.pdf", "papers/Pretrain_Knowledge-Aware_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2012.13575v1", "papers/Contextual_Temperature_for_Language_Modeling.pdf"),
    ("https://arxiv.org/pdf/2210.11610v2", "papers/Large_Language_Models_Can_Self-improve.pdf"),
    ("https://arxiv.org/pdf/2205.12986v4", "papers/Transcormer_Transformer_for_Sentence_Scoring_with_Sliding_Language_Modeling.pdf"),
    ("https://arxiv.org/pdf/2208.02169v1", "papers/SpanDrop_Simple_and_Effective_Counterfactual_Learning_for_Long_Sequences.pdf"),
    ("https://arxiv.org/pdf/2110.06773v2", "papers/Leveraging_Automated_Unit_Tests_for_Unsupervised_Code_Translation.pdf"),
    ("https://arxiv.org/pdf/2110.07280v2", "papers/P-Adapters_Robustly_Extracting_Factual_Information_from_Language_Models_with_Diverse_Prompts.pdf"),
    ("https://arxiv.org/pdf/2109.01652v5", "papers/Finetuned_Language_Models_are_Zero-Shot_Learners.pdf"),
    ("https://arxiv.org/pdf/2210.14199v1", "papers/Same_Pre-training_Loss,_Better_Downstream_Implicit_Bias_Matters_for_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2204.06863v4", "papers/ULF_UNSUPERVISED_LABELING_FUNCTION_CORRECTION_USING_CROSS-VALIDATION_FOR_WEAK_SUPERVISION.pdf"),
    ("https://arxiv.org/pdf/2202.01771v4", "papers/Pre-Trained_Language_Models_for_Interactive_Decision-Making.pdf"),
    ("https://arxiv.org/pdf/2212.10154v2", "papers/Human-Guided_Fair_Classification_for_Natural_Language_Processing.pdf"),
    ("https://arxiv.org/pdf/2203.13474v5", "papers/CodeGen_An_Open_Large_Language_Model_for_Code_with_Multi-Turn_Program_Synthesis.pdf"),
    ("https://aclanthology.org/2023.findings-acl.40.pdf", "papers/Recursion_of_Thought_Divide_and_Conquer_Reasoning_with_Language_Models.pdf"),
    ("https://aclanthology.org/2023.findings-acl.309.pdf", "papers/BertNet_Harvesting_Knowledge_Graphs_from_Pretrained_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2111.10952v2", "papers/ExT5_Towards_Extreme_Multi-Task_Scaling_for_Transfer_Learning.pdf"),
    ("https://arxiv.org/pdf/2307.10442v2", "papers/Thrust_Adaptively_Propels_Large_Language_Models_with_External_Knowledge.pdf"),
    ("https://arxiv.org/pdf/2211.01910v2", "papers/Large_Language_Models_are_Human-Level_Prompt_Engineers.pdf"),
    ("https://arxiv.org/pdf/2110.08207v3", "papers/Multitask_Prompted_Training_Enables_Zero-Shot_Task_Generalization.pdf"),
    ("https://aclanthology.org/2022.gebnlp-1.9.pdf", "papers/Quantifying_Exposure_Bias_for_Open-ended_Language_Generation.pdf"),
    ("https://arxiv.org/pdf/2108.13161v7", "papers/Differentiable_Prompt_Makes_Pre-trained_Language_Models_Better_Few-shot_Learners.pdf"),
    ("https://arxiv.org/pdf/2203.11171v4", "papers/Self-Consistency_Improves_Chain_of_Thought_Reasoning_in_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2212.14034v1", "papers/Cramming_Training_a_language_model_on_a_single_GPU_in_one_day.pdf"),
    ("https://arxiv.org/pdf/2102.01951v2", "papers/Mind_the_Gap_Assessing_Temporal_Generalization_in_Neural_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2307.09476v3", "papers/Overthinking_the_Truth_Understanding_how_Language_Models_process_False_Demonstrations.pdf"),
    ("https://arxiv.org/pdf/2201.11576v1", "papers/Grad2Task_Improved_Few-shot_Text_Classification_Using_Gradients_for_Task_Representation.pdf"),
    ("https://arxiv.org/pdf/2209.14500v2", "papers/Bidirectional_Language_Models_Are_Also_Few-shot_Learners.pdf"),
    ("https://arxiv.org/pdf/2106.09685v2", "papers/LoRA_Low-Rank_Adaptation_of_Large_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2210.01504v2", "papers/Knowledge_Unlearning_for_Mitigating_Privacy_Risks_in_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2102.08473v2", "papers/COCO-LM_Correcting_and_Contrasting_Text_Sequences_for_Language_Model_Pretraining.pdf"),
    ("https://arxiv.org/pdf/2110.02870v3", "papers/Capturing_Structural_Locality_in_Non-parametric_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2110.06500v2", "papers/Differentially_Private_Fine-tuning_of_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2010.00904v3", "papers/Autoregressive_Entity_Retrieval.pdf"),
    ("https://arxiv.org/pdf/2210.01848v2", "papers/Explaining_Patterns_in_Data_with_Language_Models_via_Interpretable_Autoprompting.pdf"),
    ("https://arxiv.org/pdf/2110.05423v1", "papers/Using_Document_Similarity_Methods_to_create_Parallel_Datasets_for_Code_Translation.pdf"),
    ("https://arxiv.org/pdf/2203.05115v2", "papers/Internet-augmented_language_models_through_few-shot_prompting_for_open-domain_question_answering.pdf"),
    ("https://arxiv.org/pdf/2110.03215v4", "papers/Towards_Continual_Knowledge_Learning_of_Language_Models.pdf"),
    ("https://arxiv.org/pdf/1911.01940v2", "papers/Deepening_Hidden_Representations_from_Pre-trained_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2209.15558v2", "papers/Out-of-Distribution_Detection_and_Selective_Generation_for_Conditional_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2210.16433v3", "papers/Knowledge-in-Context_Towards_Knowledgeable_Semi-Parametric_Language_Models.pdf"),
    ("https://ebooks.iospress.nl/pdf/doi/10.3233/FAIA220218", "papers/Interactively_Generating_Explanations_for_Transformer_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2210.01296v2", "papers/Recitation-Augmented_Language_Models.pdf"),
    ("https://arxiv.org/pdf/2210.03057v1", "papers/Language_models_are_multilingual_chain-of-thought_reasoners.pdf"),
    ("https://arxiv.org/pdf/2203.08913v1", "papers/Memorizing_Transformers.pdf"),
    ("https://arxiv.org/pdf/2107.07170v2", "papers/FLEX_Unifying_Evaluation_for_Few-Shot_NLP.pdf"),
    ("https://aclanthology.org/2024.inlg-main.34.pdf", "papers/Ensembles_and_Cocktails_Robust_Finetuning_for_Natural_Language_Generation.pdf"),
    ("https://aclanthology.org/2022.emnlp-main.651.pdf", "papers/Debiasing_Pretrained_Text_Encoders_by_Paying_Attention_to_Paying_Attention.pdf"),
    ("https://arxiv.org/pdf/2209.01975v1", "papers/Selective_Annotation_Makes_Language_Models_Better_Few-Shot_Learners.pdf"),
    ("https://arxiv.org/pdf/2110.04541v3", "papers/The_Inductive_Bias_of_In-Context_Learning_Rethinking_Pretraining_Example_Design.pdf"),
    ("https://arxiv.org/pdf/2202.00528v3", "papers/Examining_Scaling_and_Transfer_of_Language_Model_Architectures_for_Machine_Translation.pdf"),
    ("https://arxiv.org/pdf/2201.01787v2", "papers/Does_Entity_Abstraction_Help_Generative_Transformers_Reason.pdf"),
    ("https://arxiv.org/pdf/2206.04105v3", "papers/Words_are_all_you_need_Language_as_an_approximation_for_human_similarity_judgments.pdf"),
]

total = len(papers)
for i, (url, path) in enumerate(papers, 1):
    print(f"[{i}/{total}] Downloading {os.path.basename(path)}...")
    try:
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("  Saved.")
    except Exception as e:
        print(f"  Failed: {e}")

print("\nAll done!")

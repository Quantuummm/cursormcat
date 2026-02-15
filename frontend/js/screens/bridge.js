/**
 * MCAT Mastery — Bridge Mission Screen
 * 
 * Cross-subject challenge connecting two planets. Format:
 *   LYRA briefing → 3-5 hybrid questions → 1 rapid match → rewards
 * 
 * Bridges are PERMANENT — once completed, the link between planets
 * stays visible on the dashboard and Grimble can never reclaim it.
 */

// ─── Bridge Definitions ────────────────────────────────────
// Each bridge connects two subjects with MCAT-authentic cross-topic questions

const BRIDGE_DEFS = [
    {
        id: 'bio_biochem',
        planetA: 'verdania',  subjectA: 'biology',
        planetB: 'glycera',   subjectB: 'biochemistry',
        name: 'The Living Catalyst Bridge',
        briefing: "Commander, I'm detecting a signal bridge between Verdania and Glycera — where living systems meet molecular machinery. Enzyme kinetics, amino acid properties, membrane transport... the overlap is extraordinary. Clearing this will permanently weaken Grimble's hold on both worlds.",
        questions: [
            {
                stem: "Enzyme kinetics: A competitive inhibitor increases the apparent Km of an enzyme without changing Vmax. Which biological scenario best illustrates this?",
                passage: "In metabolic regulation, competitive inhibition is a common control mechanism. Malonate structurally resembles succinate and competes for the active site of succinate dehydrogenase in the TCA cycle.",
                options: [
                    { text: "Malonate competing with succinate for succinate dehydrogenase", correct: true },
                    { text: "Lead poisoning inhibiting multiple enzymes irreversibly", correct: false },
                    { text: "ATP allosterically inhibiting phosphofructokinase", correct: false },
                    { text: "Temperature denaturation of pepsin in the stomach", correct: false },
                ],
                correct_feedback: "Excellent! Malonate is a classic competitive inhibitor of succinate dehydrogenase — it mimics the substrate's structure. This is a high-yield MCAT concept bridging enzyme biochemistry with metabolic pathway biology.",
                wrong_feedback: "Review competitive vs. non-competitive vs. irreversible inhibition. Competitive inhibitors structurally resemble the substrate and bind the active site, increasing apparent Km. Malonate/succinate is the textbook example.",
            },
            {
                stem: "A mutation changes a hydrophilic amino acid in a transmembrane protein to a hydrophobic one. What is the most likely consequence for membrane transport?",
                options: [
                    { text: "The protein can no longer span the lipid bilayer", correct: false },
                    { text: "The protein's channel pore may become occluded, reducing ion transport", correct: true },
                    { text: "The protein will be targeted for lysosomal degradation", correct: false },
                    { text: "ATP hydrolysis by the protein will increase", correct: false },
                ],
                correct_feedback: "Correct! Hydrophilic residues line ion channels — replacing one with a hydrophobic residue can occlude the pore. This bridges amino acid chemistry (R-group properties) with membrane biology (channel function).",
                wrong_feedback: "Think about WHY channels work: hydrophilic amino acid side chains line the pore to allow polar/charged solutes through. Swapping to hydrophobic disrupts this selectivity filter.",
            },
            {
                stem: "Collagen requires post-translational hydroxylation of proline residues. This modification requires vitamin C as a cofactor. A patient with scurvy would show deficiency in which level of protein structure?",
                options: [
                    { text: "Primary structure", correct: false },
                    { text: "Secondary structure — the triple helix cannot form properly", correct: false },
                    { text: "Tertiary structure — the collagen triple helix is destabilized", correct: true },
                    { text: "Quaternary structure only", correct: false },
                ],
                correct_feedback: "Right! Hydroxyproline stabilizes collagen's tertiary triple-helix structure through hydrogen bonding. Without vitamin C, proline hydroxylase can't function, destabilizing the triple helix. This connects biochemical modification with protein structure biology.",
                wrong_feedback: "The collagen triple helix is a tertiary structural feature stabilized by hydroxyproline residues. Vitamin C is the cofactor for prolyl hydroxylase — without it, the helix is unstable (scurvy).",
            },
            {
                stem: "During starvation, muscle proteins are broken down and amino acids are transaminated. The carbon skeletons enter the TCA cycle while amino groups are converted to urea. Which amino acid serves as the primary carrier of amino groups from muscle to liver?",
                options: [
                    { text: "Glutamine", correct: false },
                    { text: "Alanine", correct: true },
                    { text: "Aspartate", correct: false },
                    { text: "Leucine", correct: false },
                ],
                correct_feedback: "Correct! The glucose-alanine cycle: muscle pyruvate accepts amino groups via transamination → alanine → liver → deamination → pyruvate (for gluconeogenesis) + NH4⁺ (to urea). This perfectly bridges amino acid biochemistry with systemic biology.",
                wrong_feedback: "The glucose-alanine cycle is the key concept. Muscle transamination produces alanine, which travels to the liver for deamination. Glutamine also carries NH3 but primarily from other tissues, not the muscle-liver shuttle.",
            },
        ],
        matchPairs: [
            { termA: "Michaelis-Menten (Biochem)", termB: "Enzyme regulation in metabolic pathways (Bio)" },
            { termA: "Amino acid R-groups (Biochem)", termB: "Protein function in membranes (Bio)" },
            { termA: "Protein folding (Biochem)", termB: "Collagen structure in connective tissue (Bio)" },
            { termA: "Transamination reactions (Biochem)", termB: "Nitrogen balance in fasting (Bio)" },
        ],
    },
    {
        id: 'bio_genchem',
        planetA: 'verdania',  subjectA: 'biology',
        planetB: 'luminara',  subjectB: 'gen_chem',
        name: 'The Ionic Current Bridge',
        briefing: "Commander, there's a powerful resonance between Verdania and Luminara. The chemistry of life — acid-base balance in blood, electrochemistry in neurons, osmotic forces in kidneys. This bridge is absolutely critical for MCAT success.",
        questions: [
            {
                stem: "Blood pH is maintained at 7.4 by the bicarbonate buffer system: CO₂ + H₂O ⇌ H₂CO₃ ⇌ H⁺ + HCO₃⁻. A patient hyperventilates, blowing off CO₂. According to Le Chatelier's principle, what happens?",
                options: [
                    { text: "Blood pH decreases (respiratory acidosis)", correct: false },
                    { text: "Blood pH increases (respiratory alkalosis)", correct: true },
                    { text: "Blood pH remains constant due to buffering", correct: false },
                    { text: "Bicarbonate concentration increases", correct: false },
                ],
                correct_feedback: "Correct! Removing CO₂ shifts equilibrium LEFT, consuming H⁺, raising pH → respiratory alkalosis. This is the quintessential MCAT bridge between chemical equilibrium and respiratory physiology.",
                wrong_feedback: "Le Chatelier: removing a reactant (CO₂) shifts equilibrium to consume more H⁺ (to the left), so [H⁺] drops and pH rises. Hyperventilation = less CO₂ = alkalosis.",
            },
            {
                stem: "A nerve impulse depends on the Nernst equation: E = (RT/zF)ln([ion]outside/[ion]inside). The resting membrane potential is approximately -70 mV, primarily set by K⁺ leak channels. If extracellular K⁺ concentration doubles, the resting potential will:",
                options: [
                    { text: "Become more negative (hyperpolarize)", correct: false },
                    { text: "Become less negative (depolarize)", correct: true },
                    { text: "Remain unchanged due to the Na⁺/K⁺ pump", correct: false },
                    { text: "Reverse to a positive value", correct: false },
                ],
                correct_feedback: "Correct! Increasing extracellular K⁺ reduces the concentration gradient, decreasing |E_K|. The membrane depolarizes. The Nernst equation quantifies this — it's the most-tested physics-biology-chemistry bridge on the MCAT.",
                wrong_feedback: "The Nernst equation tells us E ∝ ln([out]/[in]). Doubling [K⁺]out reduces the ratio, making E_K less negative → depolarization. The Na⁺/K⁺ pump can't compensate fast enough.",
            },
            {
                stem: "A kidney nephron reabsorbs water from the collecting duct via osmosis. The medullary interstitium has an osmolarity of 1200 mOsm/L while the tubular fluid starts at 300 mOsm/L. What thermodynamic principle drives this water movement?",
                options: [
                    { text: "Water moves down its chemical potential gradient toward lower water activity", correct: true },
                    { text: "Active transport of water by aquaporins requires ATP", correct: false },
                    { text: "Hydrostatic pressure pushes water out of the tubule", correct: false },
                    { text: "Entropy increases as solute concentration equalizes", correct: false },
                ],
                correct_feedback: "Correct! Osmosis is fundamentally about chemical potential — water moves from high water activity (dilute) to low water activity (concentrated). This connects colligative properties (gen chem) with renal physiology (biology).",
                wrong_feedback: "Osmosis occurs because water moves down its chemical potential gradient. Aquaporins are channels (passive, no ATP). The driving force is the difference in water activity between the dilute tubular fluid and concentrated medullary interstitium.",
            },
        ],
        matchPairs: [
            { termA: "Le Chatelier's principle (Chem)", termB: "Blood pH buffering system (Bio)" },
            { termA: "Nernst equation (Chem)", termB: "Resting membrane potential (Bio)" },
            { termA: "Colligative properties (Chem)", termB: "Osmosis in kidney nephrons (Bio)" },
            { termA: "Electrochemistry (Chem)", termB: "Action potential propagation (Bio)" },
        ],
    },
    {
        id: 'biochem_orgchem',
        planetA: 'glycera',   subjectA: 'biochemistry',
        planetB: 'synthara',  subjectB: 'org_chem',
        name: 'The Molecular Architecture Bridge',
        briefing: "Commander, the signal between Glycera and Synthara is strong. Organic chemistry is the language of biochemistry — functional groups, stereochemistry, reaction mechanisms all become real in biological molecules. Let's bridge these worlds.",
        questions: [
            {
                stem: "L-amino acids predominate in biological proteins. In Fischer projection, the amino group is on the LEFT for L-configuration. Using R/S nomenclature, most L-amino acids are:",
                options: [
                    { text: "S configuration", correct: true },
                    { text: "R configuration", correct: false },
                    { text: "Both R and S depending on side chain", correct: false },
                    { text: "Neither — amino acids are achiral", correct: false },
                ],
                correct_feedback: "Correct! Most L-amino acids are (S) by CIP priority rules. The exception is L-cysteine, which is (R) because sulfur's higher atomic number changes the priority ranking. Classic MCAT trap!",
                wrong_feedback: "L-amino acids are generally (S) by CIP rules. Remember: L/D is based on Fischer convention (comparison to glyceraldehyde), while R/S uses CIP priority rules. They usually align but not always (cysteine is the exception).",
            },
            {
                stem: "Serine proteases use a catalytic triad (Ser-His-Asp) for peptide bond hydrolysis. The mechanism involves Ser acting as a nucleophile. What type of organic reaction mechanism best describes the first step?",
                options: [
                    { text: "SN2 — backside attack on the carbonyl carbon", correct: false },
                    { text: "Nucleophilic acyl substitution — Ser attacks the peptide carbonyl", correct: true },
                    { text: "E1cb elimination of water from the peptide bond", correct: false },
                    { text: "Electrophilic addition to the peptide nitrogen", correct: false },
                ],
                correct_feedback: "Correct! Serine's -OH attacks the peptide carbonyl carbon in a nucleophilic acyl substitution (addition-elimination mechanism via tetrahedral intermediate). This is enzyme catalysis explained through organic mechanism!",
                wrong_feedback: "Peptide bond cleavage by serine proteases is nucleophilic acyl substitution. Serine's -OH attacks the carbonyl → tetrahedral intermediate → elimination. Not SN2 (that's on sp3 carbons, not carbonyls).",
            },
            {
                stem: "NAD⁺ accepts a hydride ion (H⁻) during dehydrogenase reactions. This is an example of what type of organic chemical transformation?",
                options: [
                    { text: "Oxidation — NAD⁺ is reduced while the substrate is oxidized", correct: true },
                    { text: "Reduction — NAD⁺ gains electrons", correct: false },
                    { text: "Substitution — hydride replaces a proton on NAD⁺", correct: false },
                    { text: "Elimination — water is removed from the substrate", correct: false },
                ],
                correct_feedback: "Correct! The substrate loses H⁻ (loses electrons = oxidation), while NAD⁺ gains H⁻ (gains electrons = reduction to NADH). Understanding oxidation/reduction in organic chemistry contexts is essential for MCAT biochemistry.",
                wrong_feedback: "NAD⁺ + H⁻ → NADH. For the SUBSTRATE: losing hydride = losing electrons = oxidation. For NAD⁺: gaining hydride = gaining electrons = reduction. The substrate is oxidized; NAD⁺ is the oxidizing agent.",
            },
        ],
        matchPairs: [
            { termA: "Stereochemistry R/S (Org Chem)", termB: "Amino acid L/D nomenclature (Biochem)" },
            { termA: "Nucleophilic acyl substitution (Org Chem)", termB: "Serine protease mechanism (Biochem)" },
            { termA: "Oxidation-reduction (Org Chem)", termB: "NAD⁺/NADH in metabolism (Biochem)" },
            { termA: "Functional group reactivity (Org Chem)", termB: "Enzyme active site chemistry (Biochem)" },
        ],
    },
    {
        id: 'physics_bio',
        planetA: 'aethon',    subjectA: 'physics',
        planetB: 'verdania',  subjectB: 'biology',
        name: 'The Biophysical Signal Bridge',
        briefing: "Commander, Aethon and Verdania share a deep connection — physics governs every biological system. Fluid dynamics in blood flow, optics in vision, electrical circuits in the nervous system. This bridge tests true interdisciplinary mastery.",
        questions: [
            {
                stem: "Blood flows through an aorta (radius 1 cm) at velocity v. It then branches into arterioles with total cross-sectional area 500 times that of the aorta. According to the continuity equation (A₁v₁ = A₂v₂), the blood velocity in the arterioles is:",
                options: [
                    { text: "500v — faster through narrower vessels", correct: false },
                    { text: "v/500 — much slower through the large total cross-section", correct: true },
                    { text: "v — velocity is maintained by the heart pump", correct: false },
                    { text: "v/√500 — Bernoulli's equation applies", correct: false },
                ],
                correct_feedback: "Correct! Continuity equation: A₁v₁ = A₂v₂. Total cross-sectional area increases 500×, so velocity decreases 500×. This slow flow in capillaries allows time for gas exchange — physics explaining biology beautifully.",
                wrong_feedback: "The continuity equation (conservation of mass for fluids) says A₁v₁ = A₂v₂. With 500× the area in arterioles, velocity must decrease 500×. This is WHY capillary flow is slow — to enable diffusion.",
            },
            {
                stem: "The human eye focuses light using a converging lens (the cornea + lens system). A person with myopia (nearsightedness) has an eyeball that is too long. What type of corrective lens is needed?",
                options: [
                    { text: "Converging lens — to add more focusing power", correct: false },
                    { text: "Diverging lens — to reduce the total refractive power", correct: true },
                    { text: "Cylindrical lens — to correct astigmatism", correct: false },
                    { text: "Prism lens — to redirect light to the retina", correct: false },
                ],
                correct_feedback: "Correct! In myopia, the focal point falls in front of the retina (eye too long). A diverging (concave) lens spreads light rays so they focus farther back, onto the retina. Optics meets anatomy!",
                wrong_feedback: "Myopia: image focuses IN FRONT of retina. Need to push the focal point back → diverge the light before it enters the eye → use a diverging (negative/concave) lens.",
            },
            {
                stem: "Sound intensity drops with distance following the inverse square law: I ∝ 1/r². A patient sits 2m from a speaker at an audiology clinic. If they move to 6m away, the perceived sound intensity becomes:",
                options: [
                    { text: "1/3 of the original", correct: false },
                    { text: "1/9 of the original", correct: true },
                    { text: "1/4 of the original", correct: false },
                    { text: "1/6 of the original", correct: false },
                ],
                correct_feedback: "Correct! I ∝ 1/r². Distance triples (2m → 6m), so intensity drops by 3² = 9. This connects wave physics with auditory perception — and hearing loss assessment in clinical settings.",
                wrong_feedback: "I ∝ 1/r². The ratio of distances is 6/2 = 3. Intensity ratio = (1/3²) = 1/9. The inverse square law governs all point-source wave phenomena: sound, light, radiation.",
            },
        ],
        matchPairs: [
            { termA: "Continuity equation / Poiseuille's law (Phys)", termB: "Blood flow in cardiovascular system (Bio)" },
            { termA: "Lens equation / Optics (Phys)", termB: "Vision & eye anatomy (Bio)" },
            { termA: "Inverse square law (Phys)", termB: "Sound perception & audiology (Bio)" },
            { termA: "Ohm's law / Circuit analysis (Phys)", termB: "Neural signaling & resistance (Bio)" },
        ],
    },
    {
        id: 'physics_genchem',
        planetA: 'aethon',    subjectA: 'physics',
        planetB: 'luminara',  subjectB: 'gen_chem',
        name: 'The Energy Nexus Bridge',
        briefing: "Commander, Aethon and Luminara resonate at the same frequency — thermodynamics in reactions, electromagnetic radiation in spectroscopy, gas laws in physiology. This bridge reveals the deepest layer of physical science on the MCAT.",
        questions: [
            {
                stem: "A spontaneous exothermic reaction has ΔH = -50 kJ/mol and ΔS = -100 J/(mol·K). At what temperature will this reaction become non-spontaneous (ΔG > 0)?",
                options: [
                    { text: "Above 500 K", correct: true },
                    { text: "Below 500 K", correct: false },
                    { text: "At all temperatures", correct: false },
                    { text: "The reaction is always spontaneous because ΔH < 0", correct: false },
                ],
                correct_feedback: "Correct! ΔG = ΔH - TΔS. At T = ΔH/ΔS = 50,000/100 = 500K, ΔG = 0. Above 500K, TΔS > |ΔH|, so ΔG > 0 (non-spontaneous). Temperature-dependent spontaneity is high-yield MCAT!",
                wrong_feedback: "ΔG = ΔH - TΔS. Both ΔH and ΔS are negative. At low T: ΔG ≈ ΔH < 0 (spontaneous). At high T: -TΔS becomes large and positive → ΔG > 0 (non-spontaneous). The crossover is at T = ΔH/ΔS = 500K.",
            },
            {
                stem: "UV-Vis spectroscopy measures electronic transitions. A conjugated diene absorbs at 217 nm. Adding two more conjugated double bonds would shift the absorption to:",
                options: [
                    { text: "Shorter wavelength (blue shift) — higher energy transitions", correct: false },
                    { text: "Longer wavelength (red shift) — lower energy HOMO-LUMO gap", correct: true },
                    { text: "No change — wavelength depends only on the functional group", correct: false },
                    { text: "The infrared region — conjugation shifts to vibrational modes", correct: false },
                ],
                correct_feedback: "Correct! More conjugation → larger delocalized π system → smaller HOMO-LUMO energy gap → lower energy photon absorbed → longer wavelength (red shift). This connects quantum mechanics, spectroscopy, and organic structure.",
                wrong_feedback: "Extended conjugation decreases the energy gap between HOMO and LUMO orbitals. ΔE = hf = hc/λ. Smaller ΔE → smaller frequency → longer wavelength. This is the red shift with conjugation rule.",
            },
            {
                stem: "A gas at 2 atm and 300 K in a 10 L container is heated to 600 K at constant volume. A valve then releases gas until the pressure returns to 2 atm while maintaining 600 K. What fraction of the gas was released?",
                options: [
                    { text: "1/4 of the gas", correct: false },
                    { text: "1/2 of the gas", correct: true },
                    { text: "3/4 of the gas", correct: false },
                    { text: "2/3 of the gas", correct: false },
                ],
                correct_feedback: "Correct! First: P₁/T₁ = P₂/T₂ → 2/300 = P₂/600 → P₂ = 4 atm. Then release gas at constant V,T until P = 2 atm: n₂/n₁ = P₂/P₁ = 2/4 = 1/2. So 1/2 the gas was released. Ideal gas law in 2 steps!",
                wrong_feedback: "Two steps: (1) Constant V: P₁/T₁ = P₂/T₂ → P₂ = 4 atm. (2) Constant V,T: release gas from 4→2 atm. Since PV = nRT at same V,T: n₂/n₁ = 2/4 = 1/2. Half the gas was released.",
            },
        ],
        matchPairs: [
            { termA: "Gibbs free energy ΔG = ΔH - TΔS (Phys)", termB: "Reaction spontaneity prediction (Chem)" },
            { termA: "Electromagnetic spectrum / E = hf (Phys)", termB: "UV-Vis / IR spectroscopy (Chem)" },
            { termA: "Ideal gas law PV = nRT (Phys)", termB: "Gas behavior & stoichiometry (Chem)" },
            { termA: "Kinetic energy ½mv² (Phys)", termB: "Maxwell-Boltzmann distribution (Chem)" },
        ],
    },
    {
        id: 'psychsoc_bio',
        planetA: 'miravel',   subjectA: 'psych_soc',
        planetB: 'verdania',  subjectB: 'biology',
        name: 'The Neurolink Bridge',
        briefing: "Commander, the connection between Miravel and Verdania is unmistakable — the mind and the body are one system. Neurotransmitters, stress hormones, sensation and perception... the MCAT loves testing where psychology meets physiology.",
        questions: [
            {
                stem: "A patient with damage to the ventromedial hypothalamus exhibits hyperphagia (overeating). This structure normally functions as a satiety center. The biological mechanism involves which signaling pathway?",
                options: [
                    { text: "Leptin signaling from adipose tissue to the hypothalamus", correct: true },
                    { text: "Dopamine reward pathway from the VTA", correct: false },
                    { text: "Cortisol feedback from the adrenal cortex", correct: false },
                    { text: "Serotonin release from the raphe nuclei", correct: false },
                ],
                correct_feedback: "Correct! Leptin (from fat cells) signals satiety via the hypothalamus. VMH damage disrupts this signal integration → constant hunger. This bridges endocrine biology with eating behavior psychology.",
                wrong_feedback: "The ventromedial hypothalamus integrates leptin signals from adipose tissue to regulate satiety. While dopamine affects reward-based eating, the primary biological mechanism for VMH satiety is leptin signaling.",
            },
            {
                stem: "The fight-or-flight response involves the sympathetic nervous system releasing norepinephrine and the adrenal medulla releasing epinephrine. These catecholamines cause all of the following EXCEPT:",
                options: [
                    { text: "Increased heart rate via β₁ adrenergic receptors", correct: false },
                    { text: "Bronchodilation via β₂ adrenergic receptors", correct: false },
                    { text: "Increased GI motility via muscarinic receptors", correct: true },
                    { text: "Glycogenolysis in the liver via β₂ receptors", correct: false },
                ],
                correct_feedback: "Correct! Increased GI motility is a PARASYMPATHETIC response (via muscarinic ACh receptors). Sympathetic activation DECREASES GI motility. This requires understanding both the psychology of stress AND the biology of autonomic signaling.",
                wrong_feedback: "Fight-or-flight (sympathetic) DECREASES GI activity — blood is diverted to muscles and brain. Increased GI motility is rest-and-digest (parasympathetic, acetylcholine on muscarinic receptors).",
            },
            {
                stem: "A researcher studies the Weber-Fechner law of perception. A participant can detect a 1 dB change in sound at 40 dB but needs a 2 dB change at 80 dB. This demonstrates:",
                options: [
                    { text: "Signal detection theory — the observer's criterion changes with intensity", correct: false },
                    { text: "Weber's law — the just noticeable difference is proportional to stimulus magnitude", correct: true },
                    { text: "Sensory adaptation — prolonged exposure reduces sensitivity", correct: false },
                    { text: "Absolute threshold — minimum detectable stimulus", correct: false },
                ],
                correct_feedback: "Correct! Weber's law states ΔI/I = constant. At higher intensity, you need a proportionally larger change to detect it. This connects psychophysics (perception) with sensory neuroscience (receptor encoding).",
                wrong_feedback: "Weber's law: ΔI/I = k (constant ratio). The just noticeable difference (JND) scales with the baseline stimulus intensity. This is why you notice a candle in a dark room but not in sunlight.",
            },
        ],
        matchPairs: [
            { termA: "Hypothalamic regulation (Psych/Soc)", termB: "Leptin/ghrelin endocrine signaling (Bio)" },
            { termA: "Fight-or-flight response (Psych/Soc)", termB: "Sympathetic nervous system (Bio)" },
            { termA: "Weber's Law perception (Psych/Soc)", termB: "Sensory receptor encoding (Bio)" },
            { termA: "Neurotransmitter effects (Psych/Soc)", termB: "Synaptic biology & receptors (Bio)" },
        ],
    },
    {
        id: 'biochem_genchem',
        planetA: 'glycera',   subjectA: 'biochemistry',
        planetB: 'luminara',  subjectB: 'gen_chem',
        name: 'The Reaction Equilibrium Bridge',
        briefing: "Commander, Glycera and Luminara pulse in harmony — equilibrium, acid-base chemistry, and redox reactions thread through every metabolic pathway. Clearing this bridge reveals how fundamental chemistry drives the machinery of life.",
        questions: [
            {
                stem: "An amino acid has pKa₁ = 2.0 (α-COOH), pKa₂ = 9.0 (α-NH₃⁺), and pKaR = 4.0 (side chain -COOH). At pH 7.0, what is the net charge on this amino acid?",
                options: [
                    { text: "+1", correct: false },
                    { text: " 0", correct: false },
                    { text: "-1", correct: true },
                    { text: "-2", correct: false },
                ],
                correct_feedback: "Correct! At pH 7.0: α-COOH (pKa 2.0) → deprotonated (-1); side chain (pKa 4.0) → deprotonated (-1); α-NH₃⁺ (pKa 9.0) → protonated (+1). Net: -1 - 1 + 1 = -1. Acid-base chemistry meets amino acid biochemistry!",
                wrong_feedback: "Compare pH to each pKa. pH 7 > pKa₁ (2.0) → COOH deprotonated = -1. pH 7 > pKaR (4.0) → side chain deprotonated = -1. pH 7 < pKa₂ (9.0) → NH₃⁺ stays protonated = +1. Net = -1.",
            },
            {
                stem: "In the electron transport chain, the standard reduction potential of NAD⁺/NADH is E° = -0.32 V and for O₂/H₂O is E° = +0.82 V. The overall ΔG° for electron transfer from NADH to O₂ is (use ΔG° = -nFΔE°):",
                options: [
                    { text: "Positive — the reaction is non-spontaneous", correct: false },
                    { text: "Negative — the large positive ΔE° drives a favorable reaction", correct: true },
                    { text: "Zero — the cell is at equilibrium", correct: false },
                    { text: "Cannot be determined without temperature", correct: false },
                ],
                correct_feedback: "Correct! ΔE° = E°(cathode) - E°(anode) = 0.82 - (-0.32) = +1.14 V. ΔG° = -nFΔE° = negative (spontaneous). This large driving force is WHY the ETC generates enough energy for ~10 ATP per NADH!",
                wrong_feedback: "ΔE° = E°(cathode, O₂) - E°(anode, NADH) = 0.82 - (-0.32) = +1.14 V > 0. ΔG° = -nFΔE° < 0 (exergonic). Positive cell potential means negative ΔG — spontaneous electron flow from NADH to O₂.",
            },
            {
                stem: "Le Chatelier's principle predicts that adding product shifts equilibrium toward reactants. In glycolysis, high ATP concentration inhibits phosphofructokinase (PFK). This regulation is best described as:",
                options: [
                    { text: "Competitive inhibition by ATP at the active site", correct: false },
                    { text: "Allosteric inhibition — a form of product feedback applying Le Chatelier's logic", correct: true },
                    { text: "Irreversible inhibition by ATP phosphorylation of PFK", correct: false },
                    { text: "Uncompetitive inhibition by ATP binding to ES complex", correct: false },
                ],
                correct_feedback: "Correct! High ATP (an 'end product' of energy metabolism) allosterically inhibits PFK, effectively shifting the pathway away from product formation. It's Le Chatelier's principle applied to metabolic flux control!",
                wrong_feedback: "ATP inhibits PFK allosterically (binds regulatory site, not active site). This is analogous to Le Chatelier: high 'product' (ATP) shifts the metabolic 'equilibrium' back. AMP/ADP activate PFK, signaling low energy.",
            },
        ],
        matchPairs: [
            { termA: "Henderson-Hasselbalch / pKa (Chem)", termB: "Amino acid charge states (Biochem)" },
            { termA: "Standard reduction potential (Chem)", termB: "Electron transport chain (Biochem)" },
            { termA: "Le Chatelier's principle (Chem)", termB: "Metabolic regulation & feedback (Biochem)" },
            { termA: "Redox half-reactions (Chem)", termB: "NAD⁺/NADH in cellular respiration (Biochem)" },
        ],
    },
];

// ─── Planet metadata for rendering ─────────────────────────
const PLANET_META = {
    verdania:  { name: 'Verdania',  emoji: '🌿', color: '#2ECC71', subject: 'Biology' },
    glycera:   { name: 'Glycera',   emoji: '🧬', color: '#E74C3C', subject: 'Biochemistry' },
    luminara:  { name: 'Luminara',  emoji: '⚡', color: '#F1C40F', subject: 'Gen. Chemistry' },
    synthara:  { name: 'Synthara',  emoji: '⚗️', color: '#9B59B6', subject: 'Org. Chemistry' },
    aethon:    { name: 'Aethon',    emoji: '🔭', color: '#3498DB', subject: 'Physics' },
    miravel:   { name: 'Miravel',   emoji: '🧠', color: '#E67E22', subject: 'Psych/Soc' },
    lexara:    { name: 'Lexara',    emoji: '📖', color: '#1ABC9C', subject: 'CARS' },
};

// ─── Bridge State ──────────────────────────────────────────

let _bridge = {
    def: null,           // Current bridge definition
    phase: 'select',     // 'select' | 'briefing' | 'question' | 'match' | 'complete'
    questionIdx: 0,
    correct: 0,
    total: 0,
    streak: 0,
    matchPairs: [],      // Shuffled match pairs
    matchSelected: null, // Currently selected match term
    matchMatched: 0,     // Number of matched pairs
    startTime: 0,
};

// ─── Init ──────────────────────────────────────────────────

function initBridge() {
    _bridge.phase = 'select';
    _renderBridgeSelect();
}

// ─── Bridge Selection Screen ───────────────────────────────

function _renderBridgeSelect() {
    const briefing = document.getElementById('bridge-briefing');
    const body = document.getElementById('bridge-body');
    
    // Determine which bridges are available vs completed vs locked
    const completed = Player.bridgesCompleted || [];
    
    briefing.innerHTML = `
        <div class="bridge-select-header">
            <div class="bridge-select-icon">🌉</div>
            <h3>Signal Bridges Detected</h3>
            <p class="bridge-select-desc">Commander, these cross-subject connections weaken Grimble's grip on multiple worlds at once. Each bridge is permanent — once stabilized, it can never be reclaimed.</p>
        </div>
    `;
    
    let cardsHtml = '';
    BRIDGE_DEFS.forEach(def => {
        const isCompleted = completed.includes(def.id);
        const isUnlocked = _isBridgeUnlocked(def);
        const metaA = PLANET_META[def.planetA];
        const metaB = PLANET_META[def.planetB];
        
        let statusClass = 'bridge-locked';
        let statusText = '🔒 Locked — clear 1 sector in both subjects';
        let clickable = false;
        
        if (isCompleted) {
            statusClass = 'bridge-completed';
            statusText = '✅ Bridge Stabilized';
        } else if (isUnlocked) {
            statusClass = 'bridge-available';
            statusText = '⚡ Signal Ready — 1 Neural Charge';
            clickable = true;
        }
        
        cardsHtml += `
            <div class="bridge-card ${statusClass}" ${clickable ? `data-bridge-id="${def.id}"` : ''}>
                <div class="bridge-card-planets">
                    <span class="bridge-planet" style="color: ${metaA.color}">${metaA.emoji} ${metaA.name}</span>
                    <span class="bridge-connector">${isCompleted ? '━━✦━━' : '╌╌╌╌╌'}</span>
                    <span class="bridge-planet" style="color: ${metaB.color}">${metaB.emoji} ${metaB.name}</span>
                </div>
                <div class="bridge-card-name">${def.name}</div>
                <div class="bridge-card-status">${statusText}</div>
            </div>
        `;
    });
    
    body.innerHTML = `<div class="bridge-card-list">${cardsHtml}</div>`;
    
    // Wire clickable cards
    body.querySelectorAll('.bridge-card.bridge-available').forEach(card => {
        card.addEventListener('click', () => {
            const bridgeId = card.getAttribute('data-bridge-id');
            const def = BRIDGE_DEFS.find(b => b.id === bridgeId);
            if (def) _startBridge(def);
        });
    });
}

function _isBridgeUnlocked(def) {
    // Bridge is unlocked when player has cleared ≥1 section in BOTH subjects
    const progressA = Player.planetProgress?.[def.planetA];
    const progressB = Player.planetProgress?.[def.planetB];
    
    const clearedA = _getProgressCount(progressA) >= 1;
    const clearedB = _getProgressCount(progressB) >= 1;
    
    return clearedA && clearedB;
}

function _getProgressCount(progress) {
    if (!progress) return 0;
    const sc = progress.sectionsCompleted;
    if (sc instanceof Set) return sc.size;
    if (Array.isArray(sc)) return sc.length;
    if (typeof sc === 'number') return sc;
    return (progress.clearedTiles?.length || 0);
}

// ─── Start Bridge Mission ──────────────────────────────────

function _startBridge(def) {
    // Check energy
    if (!hasEnergy(1)) {
        showToast('⚡ Not enough Neural Charge! Wait for recharge or use a boost.', 3000);
        return;
    }
    
    // Spend energy
    spendEnergy(1);
    
    _bridge.def = def;
    _bridge.phase = 'briefing';
    _bridge.questionIdx = 0;
    _bridge.correct = 0;
    _bridge.total = 0;
    _bridge.streak = 0;
    _bridge.matchMatched = 0;
    _bridge.matchSelected = null;
    _bridge.startTime = Date.now();
    
    // Shuffle match pairs
    _bridge.matchPairs = [...def.matchPairs].sort(() => Math.random() - 0.5);
    
    _renderBriefing();
}

// ─── LYRA Briefing ─────────────────────────────────────────

function _renderBriefing() {
    const def = _bridge.def;
    const metaA = PLANET_META[def.planetA];
    const metaB = PLANET_META[def.planetB];
    const briefing = document.getElementById('bridge-briefing');
    const body = document.getElementById('bridge-body');
    
    briefing.innerHTML = `
        <div class="bridge-visualization">
            <div class="bridge-planet-node" style="border-color: ${metaA.color}">
                <span class="planet-emoji">${metaA.emoji}</span>
                <span class="planet-label">${metaA.name}</span>
            </div>
            <div class="bridge-beam bridge-beam-charging">
                <div class="bridge-beam-particle"></div>
                <div class="bridge-beam-particle"></div>
                <div class="bridge-beam-particle"></div>
            </div>
            <div class="bridge-planet-node" style="border-color: ${metaB.color}">
                <span class="planet-emoji">${metaB.emoji}</span>
                <span class="planet-label">${metaB.name}</span>
            </div>
        </div>
    `;
    
    body.innerHTML = `
        <div class="bridge-lyra-briefing">
            <div class="lyra-avatar">🛸</div>
            <div class="lyra-bubble">
                <span class="lyra-name" style="color: var(--lyra-blue)">LYRA</span>
                <p>${def.briefing}</p>
            </div>
        </div>
        <div class="bridge-mission-info">
            <div class="mission-info-item">📝 ${def.questions.length} hybrid questions</div>
            <div class="mission-info-item">🔗 1 rapid matching round</div>
            <div class="mission-info-item">💎 40-60 crystals reward</div>
            <div class="mission-info-item">🌉 Permanent bridge link</div>
        </div>
        <button class="btn btn-primary btn-large" id="btn-begin-bridge">Begin Mission</button>
    `;
    
    // TTS
    speak(def.briefing, 'lyra');
    
    document.getElementById('btn-begin-bridge').addEventListener('click', () => {
        stopSpeaking();
        _bridge.phase = 'question';
        _renderBridgeQuestion();
    });
}

// ─── Question Phase ────────────────────────────────────────

function _renderBridgeQuestion() {
    const def = _bridge.def;
    const idx = _bridge.questionIdx;
    
    if (idx >= def.questions.length) {
        _bridge.phase = 'match';
        _renderMatchPhase();
        return;
    }
    
    const q = def.questions[idx];
    _bridge.total++;
    
    const metaA = PLANET_META[def.planetA];
    const metaB = PLANET_META[def.planetB];
    
    const briefing = document.getElementById('bridge-briefing');
    briefing.innerHTML = `
        <div class="bridge-progress">
            <div class="bridge-progress-bar">
                <div class="bridge-progress-fill" style="width: ${(idx / (def.questions.length + 1)) * 100}%"></div>
            </div>
            <span class="bridge-progress-text">Question ${idx + 1} of ${def.questions.length}</span>
            <span class="bridge-streak">${_bridge.streak > 0 ? '🔥 ' + _bridge.streak : ''}</span>
        </div>
        <div class="bridge-subjects-tag">
            <span style="color: ${metaA.color}">${metaA.emoji} ${metaA.subject}</span>
            <span> × </span>
            <span style="color: ${metaB.color}">${metaB.emoji} ${metaB.subject}</span>
        </div>
    `;
    
    const body = document.getElementById('bridge-body');
    const labels = ['A', 'B', 'C', 'D'];
    
    let optionsHtml = '';
    q.options.forEach((opt, i) => {
        optionsHtml += `
            <button class="answer-btn bridge-answer" data-idx="${i}" data-correct="${opt.correct || false}">
                <span class="answer-label">${labels[i]}</span>
                <span>${opt.text}</span>
            </button>
        `;
    });
    
    body.innerHTML = `
        <div class="bridge-question-block">
            ${q.passage ? `<div class="bridge-passage">${q.passage}</div>` : ''}
            <div class="bridge-stem">${q.stem}</div>
            <div class="bridge-options" id="bridge-options">
                ${optionsHtml}
            </div>
        </div>
    `;
    
    // Wire answers
    body.querySelectorAll('#bridge-options .answer-btn').forEach(btn => {
        btn.addEventListener('click', () => _handleBridgeAnswer(btn, q));
    });
}

function _handleBridgeAnswer(btn, q) {
    const isCorrect = btn.getAttribute('data-correct') === 'true';
    const allBtns = document.querySelectorAll('#bridge-options .answer-btn');
    
    allBtns.forEach(b => {
        b.style.pointerEvents = 'none';
        if (b.getAttribute('data-correct') === 'true') b.classList.add('correct');
    });
    
    if (isCorrect) {
        btn.classList.add('correct');
        _bridge.correct++;
        _bridge.streak++;
        _spawnBridgeVFX(btn);
    } else {
        btn.classList.add('incorrect');
        _bridge.streak = 0;
    }
    
    const feedback = isCorrect ? q.correct_feedback : q.wrong_feedback;
    const feedbackEl = document.createElement('div');
    feedbackEl.className = `bridge-feedback ${isCorrect ? 'correct' : 'incorrect'}`;
    feedbackEl.innerHTML = `
        <div class="feedback-icon">${isCorrect ? '✅' : '🔄'}</div>
        <p>${feedback}</p>
    `;
    document.getElementById('bridge-body').appendChild(feedbackEl);
    
    if (feedback) speak(feedback, isCorrect ? 'specialist' : 'lyra');
    
    const continueBtn = document.createElement('button');
    continueBtn.className = 'btn btn-primary btn-large';
    continueBtn.textContent = 'Continue';
    continueBtn.style.marginTop = '1rem';
    document.getElementById('bridge-body').appendChild(continueBtn);
    
    continueBtn.addEventListener('click', () => {
        stopSpeaking();
        _bridge.questionIdx++;
        _renderBridgeQuestion();
    });
}

// ─── Rapid Match Phase ─────────────────────────────────────

function _renderMatchPhase() {
    const def = _bridge.def;
    const metaA = PLANET_META[def.planetA];
    const metaB = PLANET_META[def.planetB];
    
    const briefing = document.getElementById('bridge-briefing');
    briefing.innerHTML = `
        <div class="bridge-progress">
            <div class="bridge-progress-bar">
                <div class="bridge-progress-fill" style="width: ${(def.questions.length / (def.questions.length + 1)) * 100}%"></div>
            </div>
            <span class="bridge-progress-text">Rapid Match — Connect the concepts!</span>
        </div>
    `;
    
    // Create two columns of shuffled terms
    const termsA = _bridge.matchPairs.map((p, i) => ({ text: p.termA, idx: i, side: 'A' }));
    const termsB = _bridge.matchPairs.map((p, i) => ({ text: p.termB, idx: i, side: 'B' }))
        .sort(() => Math.random() - 0.5);  // Shuffle B side
    
    const body = document.getElementById('bridge-body');
    body.innerHTML = `
        <div class="bridge-match-container">
            <div class="match-column match-col-a">
                <div class="match-col-header" style="color: ${metaA.color}">${metaA.emoji} ${metaA.subject}</div>
                ${termsA.map(t => `
                    <button class="match-term match-term-a" data-idx="${t.idx}" data-side="A">${t.text}</button>
                `).join('')}
            </div>
            <div class="match-column match-col-b">
                <div class="match-col-header" style="color: ${metaB.color}">${metaB.emoji} ${metaB.subject}</div>
                ${termsB.map(t => `
                    <button class="match-term match-term-b" data-idx="${t.idx}" data-side="B">${t.text}</button>
                `).join('')}
            </div>
        </div>
        <div class="match-status" id="match-status">Tap a term on the left, then its match on the right</div>
    `;
    
    _bridge.matchSelected = null;
    _bridge.matchMatched = 0;
    
    // Wire match terms
    body.querySelectorAll('.match-term').forEach(term => {
        term.addEventListener('click', () => _handleMatchClick(term));
    });
}

function _handleMatchClick(term) {
    const idx = parseInt(term.getAttribute('data-idx'));
    const side = term.getAttribute('data-side');
    
    if (term.classList.contains('matched')) return;
    
    if (!_bridge.matchSelected) {
        // First selection
        _bridge.matchSelected = { idx, side, el: term };
        term.classList.add('selected');
    } else {
        const prev = _bridge.matchSelected;
        
        // Must select from different sides
        if (prev.side === side) {
            prev.el.classList.remove('selected');
            _bridge.matchSelected = { idx, side, el: term };
            term.classList.add('selected');
            return;
        }
        
        // Check match — pair indices must be equal
        const isMatch = prev.idx === idx;
        
        if (isMatch) {
            prev.el.classList.remove('selected');
            prev.el.classList.add('matched');
            term.classList.add('matched');
            _bridge.matchMatched++;
            _bridge.correct++;
            _bridge.total++;
            
            const status = document.getElementById('match-status');
            if (_bridge.matchMatched >= _bridge.matchPairs.length) {
                status.textContent = '🎉 All connections stabilized!';
                setTimeout(() => _completeBridge(), 1200);
            } else {
                status.textContent = `✅ Connection found! ${_bridge.matchMatched}/${_bridge.matchPairs.length}`;
            }
        } else {
            prev.el.classList.remove('selected');
            prev.el.classList.add('wrong-flash');
            term.classList.add('wrong-flash');
            _bridge.total++;
            
            const status = document.getElementById('match-status');
            status.textContent = '❌ Not quite — try again';
            
            setTimeout(() => {
                prev.el.classList.remove('wrong-flash');
                term.classList.remove('wrong-flash');
            }, 600);
        }
        
        _bridge.matchSelected = null;
    }
}

// ─── Bridge Complete ───────────────────────────────────────

function _completeBridge() {
    _bridge.phase = 'complete';
    const def = _bridge.def;
    const accuracy = _bridge.total > 0 ? _bridge.correct / _bridge.total : 1;
    const baseCrystals = 40;
    const crystals = Math.round(baseCrystals + (accuracy * 20)); // 40-60
    const perfectBonus = accuracy === 1 ? 25 : 0;
    const totalCrystals = crystals + perfectBonus;
    
    // Mark bridge as completed in player state
    if (!Player.bridgesCompleted) Player.bridgesCompleted = [];
    if (!Player.bridgesCompleted.includes(def.id)) {
        Player.bridgesCompleted.push(def.id);
    }
    
    // Save player state
    _saveLocal();
    
    // Update daily streak
    if (typeof updateDailyStreak === 'function') updateDailyStreak();
    
    const metaA = PLANET_META[def.planetA];
    const metaB = PLANET_META[def.planetB];
    
    const briefing = document.getElementById('bridge-briefing');
    briefing.innerHTML = `
        <div class="bridge-visualization bridge-complete-viz">
            <div class="bridge-planet-node bridge-node-glow" style="border-color: ${metaA.color}">
                <span class="planet-emoji">${metaA.emoji}</span>
                <span class="planet-label">${metaA.name}</span>
            </div>
            <div class="bridge-beam bridge-beam-active">
                <div class="bridge-beam-core"></div>
                <span class="bridge-beam-status">✦ STABILIZED ✦</span>
            </div>
            <div class="bridge-planet-node bridge-node-glow" style="border-color: ${metaB.color}">
                <span class="planet-emoji">${metaB.emoji}</span>
                <span class="planet-label">${metaB.name}</span>
            </div>
        </div>
    `;
    
    const elapsed = Math.round((Date.now() - _bridge.startTime) / 1000);
    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    
    const body = document.getElementById('bridge-body');
    body.innerHTML = `
        <div class="bridge-complete-panel">
            <h3 class="bridge-complete-title">🌉 Bridge Stabilized!</h3>
            <p class="bridge-complete-name">${def.name}</p>
            
            <div class="bridge-stats-grid">
                <div class="bridge-stat">
                    <span class="bridge-stat-value">${Math.round(accuracy * 100)}%</span>
                    <span class="bridge-stat-label">Accuracy</span>
                </div>
                <div class="bridge-stat">
                    <span class="bridge-stat-value">${_bridge.correct}/${_bridge.total}</span>
                    <span class="bridge-stat-label">Correct</span>
                </div>
                <div class="bridge-stat">
                    <span class="bridge-stat-value">${mins}:${secs.toString().padStart(2, '0')}</span>
                    <span class="bridge-stat-label">Time</span>
                </div>
            </div>
            
            <div class="bridge-rewards">
                <div class="reward-row">✨ ${totalCrystals} Crystals${perfectBonus > 0 ? ' (includes +25 perfect bonus!)' : ''}</div>
                <div class="reward-row">🌉 Permanent bridge link on dashboard</div>
                <div class="reward-row">⭐ +250 XP Bridge Completion</div>
            </div>
            
            <button class="btn btn-primary btn-large" id="btn-bridge-done">Return to Dashboard</button>
        </div>
    `;
    
    // Grant rewards
    if (typeof addCrystals === 'function') addCrystals(totalCrystals);
    
    // LYRA congratulations
    speak("Bridge stabilized, Commander! This connection between worlds is permanent — Grimble can never break it. Your cross-subject mastery grows stronger.", 'lyra');
    
    document.getElementById('btn-bridge-done').addEventListener('click', () => {
        stopSpeaking();
        showScreen('dashboard-screen');
        if (typeof updateHUD === 'function') updateHUD();
    });
}

// ─── VFX ───────────────────────────────────────────────────

function _spawnBridgeVFX(targetEl) {
    const rect = targetEl.getBoundingClientRect();
    
    // Crystal popup
    const popup = document.createElement('div');
    popup.className = 'crystal-popup';
    popup.textContent = '⚡';
    popup.style.left = `${rect.right - 20}px`;
    popup.style.top = `${rect.top}px`;
    document.body.appendChild(popup);
    setTimeout(() => popup.remove(), 1100);
    
    // Resonance ring
    const ring = document.createElement('div');
    ring.className = 'resonance-vfx';
    ring.style.left = `${rect.left + rect.width / 2 - 60}px`;
    ring.style.top = `${rect.top + rect.height / 2 - 60}px`;
    document.body.appendChild(ring);
    setTimeout(() => ring.remove(), 700);
}

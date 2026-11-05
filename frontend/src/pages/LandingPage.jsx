import { Link } from 'react-router-dom'
import {
  BookOpen,
  Brain,
  ShieldCheck,
  Cpu,
  Sparkles,
  ArrowRight,
  FileCheck,
  Layers,
  GraduationCap,
  Scale,
  Award,
  BarChart,
  CheckCircle2,
} from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-cream text-charcoal flex flex-col font-sans selection:bg-terracotta/20">
      {/* Top Navigation */}
      <header className="border-b border-sand bg-ivory/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-18 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-terracotta rounded-xl flex items-center justify-center shadow-soft">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-display text-2xl font-bold tracking-tight text-charcoal">ExamForge</span>
              <span className="block text-[10px] font-semibold text-terracotta uppercase tracking-widest -mt-1">
                Autonomous Academic Examiner
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="text-sm font-semibold text-charcoal hover:text-terracotta px-4 py-2 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="btn-primary text-sm shadow-soft hover:shadow-card transition-all"
            >
              Start Assessment
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-6 max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sand/60 border border-sand text-xs font-semibold text-charcoal/80 mb-6">
          <Sparkles className="w-3.5 h-3.5 text-terracotta" />
          Real Dual-Engine AI: Google Gemini + IBM Granite via watsonx.ai
        </div>

        <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold text-charcoal tracking-tight leading-[1.1] mb-8">
          The Autonomous AI Academic <span className="italic text-terracotta font-serif">Examiner</span>.
        </h1>

        <p className="text-lg sm:text-xl text-warmgray max-w-3xl mx-auto font-normal leading-relaxed mb-10">
          ExamForge is not a quiz app or textbook chatbot. It is an intelligent oral examiner that ingests your academic
          documents, interrogates your understanding dynamically, semantically evaluates reasoning with IBM Granite,
          and validates genuine mastery.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/register"
            className="btn-primary text-base px-8 py-3.5 rounded-xl shadow-card hover:scale-[1.02] transition-transform w-full sm:w-auto"
          >
            Start Your Academic Examination
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/login"
            className="btn-secondary text-base px-8 py-3.5 rounded-xl border border-sand bg-ivory text-charcoal hover:bg-sand/60 transition-colors w-full sm:w-auto"
          >
            Sign In to Profile
          </Link>
        </div>
      </section>

      {/* Dual-Engine AI Architecture Diagram */}
      <section className="py-16 px-6 max-w-5xl mx-auto">
        <div className="card bg-white border border-sand p-8 sm:p-12 shadow-card rounded-2xl relative overflow-hidden">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <h2 className="text-3xl font-display font-bold text-charcoal mb-3">Six-Agent Real AI Architecture</h2>
            <p className="text-sm text-warmgray">
              Each turn executes actual model inference across Google Gemini and IBM Granite orchestrated with LangGraph.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Gemini Column */}
            <div className="bg-ivory/60 rounded-xl p-6 border border-sand">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-8 h-8 rounded-lg bg-terracotta/20 text-terracotta flex items-center justify-center font-bold text-xs">
                  G
                </div>
                <div>
                  <h3 className="text-base font-bold text-charcoal">Google Gemini</h3>
                  <p className="text-xs text-warmgray">Document Understanding, Question Authoring & Examination</p>
                </div>
              </div>

              <ul className="space-y-3.5 text-xs text-charcoal/80">
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sage flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-charcoal block">Agent 1: Document Understanding</strong>
                    Extracts complete hierarchical knowledge map, formulas, definitions, and page references.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sage flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-charcoal block">Agent 2: Question Generation</strong>
                    Authors 8-category question banks (Definition, Conceptual, Tricky, Application, Analytical).
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sage flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-charcoal block">Agent 3: Autonomous Examiner</strong>
                    Acts as human professor; receives previous answers & Granite evaluations to formulate adaptive follow-ups.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sage flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-charcoal block">Agent 4: Final Report Generation</strong>
                    Synthesizes comprehensive performance narrative and prioritized revision roadmaps from real evidence.
                  </div>
                </li>
              </ul>
            </div>

            {/* Granite Column */}
            <div className="bg-ivory/60 rounded-xl p-6 border border-sand">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-8 h-8 rounded-lg bg-sage/20 text-sage flex items-center justify-center font-bold text-xs">
                  IBM
                </div>
                <div>
                  <h3 className="text-base font-bold text-charcoal">IBM Granite via watsonx.ai</h3>
                  <p className="text-xs text-warmgray">Semantic Evaluation & Cumulative Knowledge Assessment</p>
                </div>
              </div>

              <ul className="space-y-3.5 text-xs text-charcoal/80">
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sage flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-charcoal block">Agent 5: Answer Evaluation Agent</strong>
                    Evaluates 5 weighted criteria: Correctness (30%), Completeness (25%), Conceptual Understanding (20%), Reasoning (15%), Application (10%).
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sage flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-charcoal block">Agent 6: Knowledge Assessment Agent</strong>
                    Determines topic mastery: Strong, Partially Understood, Weak, or Not Assessed using semantic evidence.
                  </div>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-sage flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-charcoal block">Semantic Equivalence Recognition</strong>
                    Awards credit for authentic comprehension in the student's own words while penalizing rote keyword stuffing.
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section className="py-16 px-6 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-charcoal mb-3">How the Examination Lifecycle Works</h2>
          <p className="text-sm text-warmgray">
            A continuous evidence-driven loop that adapts to your actual demonstrated competence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card p-6 bg-white border border-sand">
            <div className="w-9 h-9 rounded-lg bg-terracotta/15 text-terracotta flex items-center justify-center font-bold mb-4">
              1
            </div>
            <h3 className="font-bold text-base text-charcoal mb-2">Upload Material</h3>
            <p className="text-xs text-warmgray leading-relaxed">
              Upload your syllabus, textbook, or lecture notes. PyMuPDF extracts text with OCR fallback and ChromaDB indexes vectors.
            </p>
          </div>

          <div className="card p-6 bg-white border border-sand">
            <div className="w-9 h-9 rounded-lg bg-terracotta/15 text-terracotta flex items-center justify-center font-bold mb-4">
              2
            </div>
            <h3 className="font-bold text-base text-charcoal mb-2">Deconstruct</h3>
            <p className="text-xs text-warmgray leading-relaxed">
              Gemini analyzes the document into structured subjects, modules, topics, formulas, definitions, and grounded questions.
            </p>
          </div>

          <div className="card p-6 bg-white border border-sand">
            <div className="w-9 h-9 rounded-lg bg-terracotta/15 text-terracotta flex items-center justify-center font-bold mb-4">
              3
            </div>
            <h3 className="font-bold text-base text-charcoal mb-2">Oral Examination</h3>
            <p className="text-xs text-warmgray leading-relaxed">
              Gemini asks targeted questions one at a time. IBM Granite scores each answer semantically and flags specific misconceptions.
            </p>
          </div>

          <div className="card p-6 bg-white border border-sand">
            <div className="w-9 h-9 rounded-lg bg-terracotta/15 text-terracotta flex items-center justify-center font-bold mb-4">
              4
            </div>
            <h3 className="font-bold text-base text-charcoal mb-2">Mastery Report</h3>
            <p className="text-xs text-warmgray leading-relaxed">
              Receive an evidence-backed knowledge profile, strength/gap analysis, prioritized revision guide, and authenticated PDF export.
            </p>
          </div>
        </div>
      </section>

      {/* Professional Footer */}
      <footer className="mt-auto border-t border-sand bg-ivory/60 py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6 text-xs text-warmgray">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-terracotta rounded-md flex items-center justify-center">
              <BookOpen className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-display text-base font-bold text-charcoal">ExamForge</span>
            <span>· Academic Intelligence Platform</span>
          </div>

          <div className="flex items-center gap-6 font-medium">
            <Link to="/login" className="hover:text-terracotta transition-colors">
              Sign In
            </Link>
            <Link to="/register" className="hover:text-terracotta transition-colors">
              Register
            </Link>
            <span className="text-sand">|</span>
            <span>Powered by Google Gemini & IBM Granite</span>
          </div>
        </div>
      </footer>
    </div>
  )
}


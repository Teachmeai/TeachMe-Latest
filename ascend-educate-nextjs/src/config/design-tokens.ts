/**
 * Design System Tokens
 * 
 * Centralized design constants for consistent spacing, typography, and styling
 * across the profile management and form components.
 * 
 * @usage Import and use these tokens instead of hardcoded Tailwind classes
 * @example 
 * import { SPACING, PADDING } from '@/config/design-tokens'
 * className={SPACING.form.betweenFields}
 */

export const SPACING = {
  // Vertical spacing between elements
  form: {
    betweenLabelAndInput: 'space-y-2',    // Label → Input
    betweenFields: 'space-y-4',           // Field → Field
    betweenSections: 'space-y-6',         // Section → Section
    betweenContainers: 'space-y-8',       // Top-level containers (rarely used)
  },
  
  // Grid gaps
  grid: {
    formFields: 'gap-5',                  // Form field grids
    cards: 'gap-5',                       // Card grids
    inline: 'gap-3',                      // Inline elements (buttons, badges)
    tight: 'gap-2',                       // Tight inline spacing
  },
  
  // Flex gaps
  flex: {
    default: 'gap-3',
    tight: 'gap-2',
    loose: 'gap-4',
  }
} as const

export const PADDING = {
  // Container padding
  container: {
    small: 'p-4',                         // Small cards, inline elements
    medium: 'p-5',                        // Form containers (most common)
    large: 'p-6',                         // Major section containers
  },
  
  // Specific use cases
  sectionHeader: 'p-5',                   // Section headers
  card: 'p-4',                            // Info cards
  modalHeader: 'p-6',                     // Modal header
  modalContent: 'p-6 pb-8',               // Modal content area
} as const

export const TYPOGRAPHY = {
  // Headings
  heading: {
    page: 'text-2xl font-bold',           // Main page title
    section: 'text-lg font-semibold',     // Section headers
    subsection: 'text-base font-semibold', // Subsections
    card: 'text-sm font-semibold',        // Card titles
  },
  
  // Labels
  label: {
    default: 'text-sm font-medium',       // Form labels
    large: 'text-base font-semibold',     // Prominent labels
  },
  
  // Body text
  body: {
    default: 'text-base',                 // Regular text
    small: 'text-sm',                     // Helper text, descriptions
    muted: 'text-sm text-muted-foreground', // Muted helper text
  },
  
  // Input text
  input: {
    size: 'text-base',                    // Input text size
    height: 'h-12',                       // Input height
  }
} as const

export const BORDER_RADIUS = {
  default: 'rounded-lg',                  // Standard border radius
  card: 'rounded-lg',                     // Cards
  button: 'rounded-lg',                   // Buttons
  input: 'rounded-lg',                    // Form inputs (default from shadcn)
  full: 'rounded-full',                   // Pills, badges
} as const

export const BACKGROUNDS = {
  // Subtle backgrounds
  muted: {
    subtle: 'bg-muted/20',                // Very subtle background
    light: 'bg-muted/30',                 // Light background
    medium: 'bg-muted/50',                // Medium background
  },
  
  // Card backgrounds
  card: {
    default: 'bg-card',
    subtle: 'bg-card/50',
  },
  
  // Gradient backgrounds (use sparingly)
  gradient: {
    subtle: 'bg-gradient-to-r from-muted/20 to-muted/10',
  }
} as const

export const BORDERS = {
  default: 'border border-border/30',     // Standard border (subtle and professional)
  subtle: 'border border-border/20',      // Very subtle
  prominent: 'border border-border/40',   // More visible (for emphasis)
} as const

export const TRANSITIONS = {
  // Hover effects
  button: 'transition-all duration-200',
  card: 'transition-colors duration-200',
  
  // Animations
  fadeIn: 'animate-fade-in',
  scaleIn: 'animate-scale-in',
} as const

/**
 * Helper function to combine design tokens
 * @example combineTokens(SPACING.form.betweenFields, PADDING.container.medium)
 */
export function combineTokens(...tokens: string[]): string {
  return tokens.join(' ')
}

/**
 * Design System Usage Guidelines:
 * 
 * 1. SPACING:
 *    - Use space-y-2 between label and input
 *    - Use space-y-4 between form fields
 *    - Use space-y-6 between major sections
 *    - Use gap-5 for form field grids
 * 
 * 2. PADDING:
 *    - Use p-5 for most form containers
 *    - Use p-4 for cards and smaller elements
 *    - Use p-6 for major section containers
 * 
 * 3. TYPOGRAPHY:
 *    - Page titles: text-2xl font-bold
 *    - Section headers: text-lg font-semibold
 *    - Labels: text-sm font-medium
 *    - Body/Input: text-base
 *    - Helper text: text-sm text-muted-foreground
 * 
 * 4. CONSISTENCY:
 *    - Prefer design tokens over hardcoded classes
 *    - Update tokens here rather than in components
 *    - Keep visual consistency across all forms
 */


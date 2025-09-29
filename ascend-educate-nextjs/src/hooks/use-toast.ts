import * as React from "react";

import type { ToastActionElement, ToastProps } from "@/components/ui/toast";

const TOAST_LIMIT = 1;

type ToasterToast = ToastProps & {
  id: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: ToastActionElement;
};

let count = 0;

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER;
  return count.toString();
}

type Action =
  | {
      type: "ADD_TOAST";
      toast: ToasterToast;
    }
  | {
      type: "UPDATE_TOAST";
      toast: Partial<ToasterToast>;
    }
  | {
      type: "DISMISS_TOAST";
      toastId?: ToasterToast["id"];
    }
  | {
      type: "REMOVE_TOAST";
      toastId?: ToasterToast["id"];
    };

interface State {
  toasts: ToasterToast[];
}

export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case "ADD_TOAST":
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      };

    case "UPDATE_TOAST":
      return {
        ...state,
        toasts: state.toasts.map((t) => (t.id === action.toast.id ? { ...t, ...action.toast } : t)),
      };

    case "DISMISS_TOAST": {
      const { toastId } = action;

      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId || toastId === undefined
            ? {
                ...t,
                open: false,
              }
            : t,
        ),
      };
    }
    case "REMOVE_TOAST":
      if (action.toastId === undefined) {
        return {
          ...state,
          toasts: [],
        };
      }
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toastId),
      };
  }
};

// Create a context for toast state management
const ToastContext = React.createContext<{
  state: State;
  dispatch: (action: Action) => void;
} | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = React.useState<State>({ toasts: [] });

  const dispatch = React.useCallback((action: Action) => {
    setState(prevState => reducer(prevState, action));
  }, []);

  return React.createElement(
    ToastContext.Provider,
    { value: { state, dispatch } },
    children
  );
}

type Toast = Omit<ToasterToast, "id">;

function useToast() {
  const context = React.useContext(ToastContext);
  
  if (!context) {
    // Fallback for when context is not available
    return {
      toasts: [],
      toast: () => ({ id: '', dismiss: () => {}, update: () => {} }),
      dismiss: () => {},
    };
  }

  const toast = (props: Toast) => {
    const id = genId();
    const toastData = { ...props, id };

    context.dispatch({
      type: "ADD_TOAST",
      toast: toastData,
    });

    const update = (updateProps: ToasterToast) => {
      context.dispatch({
        type: "UPDATE_TOAST",
        toast: { ...updateProps, id },
      });
    };
    
    const dismiss = () => {
      context.dispatch({
        type: "DISMISS_TOAST",
        toastId: id,
      });
    };

    return {
      id: id,
      dismiss,
      update,
    };
  };

  return {
    ...context.state,
    toast,
    dismiss: (toastId?: string) => context.dispatch({ type: "DISMISS_TOAST", toastId }),
  };
}

export { useToast };

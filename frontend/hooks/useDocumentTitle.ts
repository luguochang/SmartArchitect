/**
 * useDocumentTitle Hook
 *
 * A React hook for dynamically updating the document title
 * with proper cleanup and optional suffix
 *
 * Usage:
 *   import { useDocumentTitle } from '@/hooks/useDocumentTitle';
 *
 *   function MyComponent() {
 *     const nodeCount = useArchitectStore(s => s.nodes.length);
 *     useDocumentTitle(`${nodeCount} nodes`);
 *     // Result: "12 nodes | Archboard"
 *   }
 */

import { useEffect, useRef } from 'react';

interface UseDocumentTitleOptions {
  /**
   * Whether to append " | Archboard" suffix
   * @default true
   */
  suffix?: boolean;

  /**
   * Custom suffix to use instead of default
   * @default "Archboard"
   */
  customSuffix?: string;

  /**
   * Whether to restore previous title on unmount
   * @default false
   */
  restoreOnUnmount?: boolean;
}

export function useDocumentTitle(
  title: string,
  options: UseDocumentTitleOptions = {}
) {
  const {
    suffix = true,
    customSuffix = 'Archboard',
    restoreOnUnmount = false
  } = options;

  const prevTitleRef = useRef<string>();

  useEffect(() => {
    // Store previous title on first render
    if (prevTitleRef.current === undefined) {
      prevTitleRef.current = document.title;
    }

    // Update title
    const fullTitle = suffix
      ? `${title} | ${customSuffix}`
      : title;

    document.title = fullTitle;

    // Cleanup: restore previous title if requested
    return () => {
      if (restoreOnUnmount && prevTitleRef.current) {
        document.title = prevTitleRef.current;
      }
    };
  }, [title, suffix, customSuffix, restoreOnUnmount]);
}

/**
 * useStatusTitle Hook
 *
 * Specialized hook for showing status indicators in title
 * Useful for unsaved changes, loading states, notifications
 *
 * Usage:
 *   const { setStatus, clearStatus } = useStatusTitle('Canvas');
 *
 *   // Show unsaved indicator
 *   setStatus('unsaved', { prefix: '*' });
 *   // Result: "* Canvas | Archboard"
 *
 *   // Show loading
 *   setStatus('loading', { prefix: '⏳' });
 *   // Result: "⏳ Canvas | Archboard"
 */

export function useStatusTitle(baseTitle: string) {
  const statusRef = useRef<string | null>(null);
  const prefixRef = useRef<string>('');

  const updateTitle = () => {
    const prefix = prefixRef.current ? `${prefixRef.current} ` : '';
    const fullTitle = `${prefix}${baseTitle} | Archboard`;
    document.title = fullTitle;
  };

  useEffect(() => {
    updateTitle();
  }, [baseTitle]);

  const setStatus = (status: string, options: { prefix?: string } = {}) => {
    statusRef.current = status;
    prefixRef.current = options.prefix || '';
    updateTitle();
  };

  const clearStatus = () => {
    statusRef.current = null;
    prefixRef.current = '';
    updateTitle();
  };

  return { setStatus, clearStatus };
}

/**
 * useNotificationTitle Hook
 *
 * Shows notification count in title (like "(3) Messages | Archboard")
 * Useful for background notifications, unread messages, etc.
 *
 * Usage:
 *   const setCount = useNotificationTitle('Messages');
 *   setCount(3);  // "(3) Messages | Archboard"
 *   setCount(0);  // "Messages | Archboard"
 */

export function useNotificationTitle(baseTitle: string) {
  const countRef = useRef<number>(0);

  const updateTitle = (count: number) => {
    countRef.current = count;
    const prefix = count > 0 ? `(${count}) ` : '';
    document.title = `${prefix}${baseTitle} | Archboard`;
  };

  useEffect(() => {
    updateTitle(0);
  }, [baseTitle]);

  return updateTitle;
}

/**
 * Example usage in components
 */

// Example 1: Dynamic node count
/*
function ArchitectCanvas() {
  const nodes = useArchitectStore(s => s.nodes);
  useDocumentTitle(
    nodes.length > 0 ? `${nodes.length} nodes` : 'Canvas'
  );

  return <div>Canvas content...</div>;
}
*/

// Example 2: Unsaved changes indicator
/*
function Editor() {
  const hasChanges = useArchitectStore(s => s.hasUnsavedChanges);
  const { setStatus, clearStatus } = useStatusTitle('Editor');

  useEffect(() => {
    if (hasChanges) {
      setStatus('unsaved', { prefix: '*' });
    } else {
      clearStatus();
    }
  }, [hasChanges]);

  return <div>Editor content...</div>;
}
*/

// Example 3: Loading state
/*
function DataLoader() {
  const [isLoading, setIsLoading] = useState(false);
  const { setStatus, clearStatus } = useStatusTitle('Dashboard');

  useEffect(() => {
    if (isLoading) {
      setStatus('loading', { prefix: '⏳' });
    } else {
      clearStatus();
    }
  }, [isLoading]);

  return <div>Dashboard content...</div>;
}
*/

// Example 4: Notification count
/*
function NotificationCenter() {
  const notifications = useNotifications();
  const setCount = useNotificationTitle('Notifications');

  useEffect(() => {
    const unreadCount = notifications.filter(n => !n.read).length;
    setCount(unreadCount);
  }, [notifications]);

  return <div>Notifications...</div>;
}
*/

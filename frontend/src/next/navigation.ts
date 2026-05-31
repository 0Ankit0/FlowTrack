import { useCallback, useMemo } from 'react';
import {
  useLocation,
  useNavigate,
  useParams as useReactRouterParams,
  useSearchParams as useReactRouterSearchParams,
} from 'react-router-dom';

type NavigateOptions = {
  scroll?: boolean;
  forceOptimisticNavigation?: boolean;
};

export function useRouter() {
  const navigate = useNavigate();

  const push = useCallback(
    (href: string, _options?: NavigateOptions) => {
      navigate(href);
    },
    [navigate]
  );

  const replace = useCallback(
    (href: string, _options?: NavigateOptions) => {
      navigate(href, { replace: true });
    },
    [navigate]
  );

  const refresh = useCallback(() => {
    navigate(0);
  }, [navigate]);

  return useMemo(
    () => ({
      push,
      replace,
      refresh,
      back: () => navigate(-1),
      forward: () => navigate(1),
      prefetch: async () => Promise.resolve(),
    }),
    [navigate, push, refresh, replace]
  );
}

export function usePathname() {
  return useLocation().pathname;
}

export function useSearchParams() {
  const [searchParams] = useReactRouterSearchParams();
  return searchParams;
}

export function useParams<T extends Record<string, string | undefined> = Record<string, string | undefined>>() {
  return useReactRouterParams<T>();
}

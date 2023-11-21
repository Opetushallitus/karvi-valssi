(ns oph.common.infra.csrf-token
  (:import java.util.Random
           java.util.UUID)
  (:require [clojure.tools.logging :as log]
            [ring.util.http-response :as response]
            [arvo.config :refer [env]]))

;;Double submit cookies: https://www.owasp.org/index.php/Cross-Site_Request_Forgery_%28CSRF%29_Prevention_Cheat_Sheet#Double_Submit_Cookies

(defn validi-csrf-token? [request]
  (let [xsrf-cookie-value (get-in request [:cookies "XSRF-TOKEN" :value])
        xsrf-header-value (or (get-in request [:headers "x-xsrf-token"])
                              (get-in request [:multipart-params "x-xsrf-token"]))
        csrf-protection-disabled? (get-in env [:ominaisuus :allow-cors-requests])]
    (or csrf-protection-disabled?
        (and
         xsrf-cookie-value
         xsrf-header-value
         (.equals xsrf-header-value xsrf-cookie-value)))))

(defn wrap-tarkasta-csrf-token [ring-handler]
  (fn [request]
    (if (validi-csrf-token? request)
      (ring-handler request)
      (do
        (log/error "Virheellinen XSRF-TOKEN.")
        (response/unauthorized)))))

(defn aseta-csrf-token [service-path]
  (let [random (java.util.Random.)
        token (java.util.UUID. (.nextLong random) (.nextLong random)) ;;Käytetään randomia, jotta entropian loppuminen ei aiheuta ongelmia.
        csrf-protection-disabled? (get-in env [:ominaisuus :allow-cors-requests])
        same-site (if csrf-protection-disabled? "None" "Lax")]
    (str "XSRF-TOKEN=" token "; Path=/;Secure;SameSite=" same-site)))

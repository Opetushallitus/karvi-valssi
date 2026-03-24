import {lazy, Suspense, useEffect} from 'react';
import {BrowserRouter as Router, Route, Routes, useLocation} from 'react-router-dom';
import SnackBarAlert, {StickyAlert} from '@cscfi/shared/components/Alert/Alert';
import LoadingIndicator from '@cscfi/shared/components/Loading/LoadingIndicator';
import {ThemeProvider} from '@mui/material/styles';
import theme from '@cscfi/shared/theme';
import {useObservableState} from 'observable-hooks';
import {casHostname} from '@cscfi/shared/services/Settings/Settings-service';
import {clearSession, logoutFromValssi$} from '@cscfi/shared/services/Http/Http-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {allowedRoles, userInfo$} from '@cscfi/shared/services/Login/Login-service';
import {virkailijapalveluGetMessages$} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {useTranslation} from 'react-i18next';
import VirkailijaNavigaatio from './components/Navigaatio/VirkailijaNavigaatio';
import VirkailijaAlatunniste from './components/Navigaatio/Alatunniste/VirkailijaAlatunniste';
import {GuardedRoute} from './components/GuardedRoute/GuardedRoute';
import UserContext from './Context';

const RakennaKysely = lazy(() => import('./pages/RakennaKysely/RakennaKysely'));
const Login = lazy(() => import('./components/Login/Login'));
const Etusivu = lazy(() => import('./pages/Etusivu/Etusivu'));
const Indikaattorit = lazy(() => import('./pages/Indikaattorit/Indikaattorit'));
const Tiedonkeruu = lazy(() => import('./pages/Tiedonkeruu/Tiedonkeruu'));
const Raportointi = lazy(() => import('./pages/Raportointi/Raportointi'));
const Aluejako = lazy(() => import('./pages/Aluejako/Aluejako'));
const MuokkaaAluetta = lazy(() => import('./pages/Aluejako/UusiAlue/MuokkaaAluetta'));
const MuokkaaLisaaRaportointiPohja = lazy(
    () => import('./pages/RaportointiPohja/MuokkaaLisaaRaportointiPohja'),
);
const RaportointiPohjaEsikatselu = lazy(
    () => import('./pages/RaportointiPohja/RaporttiPohjaEsikatselu'),
);
const Yhteenveto = lazy(() => import('./pages/Yhteenveto/Yhteenveto'));
const YhteenvetoList = lazy(() => import('./pages/Yhteenveto/YhteenvetoList'));
const Arviointitulokset = lazy(
    () => import('./pages/Arviointitulokset/Arviointitulokset'),
);
const Esikatselu = lazy(() => import('./pages/Esikatselu/Esikatselu'));
const Aktivointi = lazy(() => import('./pages/Aktivointi/Aktivointi'));
const Lahetys = lazy(() => import('./pages/Lahetys/Lahetys'));
const TyontekijatVardastaLahetys = lazy(
    () => import('./pages/Lahetys/TyontekijatVardastaLahetys'),
);
const SimpleError = lazy(() => import('./components/SimpleError/SimpleError'));

function App() {
    const basename = import.meta.env.MODE === 'test' ? '' : '/virkailija-ui/';
    const [originalUserInfo] = useObservableState(() => userInfo$, undefined);
    const [msg] = useObservableState(() => virkailijapalveluGetMessages$());
    const {
        i18n,
        i18n: {language: lang},
    } = useTranslation();
    i18n.loadLanguages(['fi', 'sv', 'en']);
    if (msg?.message) console.info('app msg', msg);

    logoutFromValssi$.subscribe((logout: boolean) => {
        if (logout) {
            const alert = {
                title: {key: 'warning-logout-title', ns: 'yleiset'},
                severity: 'warning',
            } as AlertType;
            AlertService.showAlert(alert);
            setTimeout(() => {
                clearSession();
                window.location.href = `${casHostname}logout`;
            }, 5000);
        }
    });

    useEffect(() => {
        document.documentElement.setAttribute('lang', lang);
    }, [lang]);

    const LahetysWithKey = () => {
        const location = useLocation();
        return <Lahetys key={location.search} />;
    };

    return (
        <ThemeProvider theme={theme}>
            <UserContext.Provider value={originalUserInfo}>
                <div className="app">
                    <StickyAlert />
                    <SnackBarAlert />
                    <LoadingIndicator />
                    <Router basename={basename}>
                        <div className="page-wrapper">
                            <VirkailijaNavigaatio />
                            <Suspense fallback={<LoadingIndicator alwaysLoading />}>
                                <main className="content">
                                    <Routes>
                                        <Route
                                            path="/"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.etusivu}
                                                >
                                                    <Etusivu />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/indikaattorit"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.indikaattorit}
                                                >
                                                    <Indikaattorit />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/tiedonkeruu"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.tiedonkeruu}
                                                >
                                                    <Tiedonkeruu />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/raportointi"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.raportointi}
                                                >
                                                    <Raportointi />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/aluejako"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.aluejako}
                                                >
                                                    <Aluejako />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/aluejako/uusi"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.aluejako}
                                                >
                                                    <MuokkaaAluetta />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/aluejako/muokkaa/:alueId"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.aluejako}
                                                >
                                                    <MuokkaaAluetta />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/raportointipohja"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.raporttipohja}
                                                >
                                                    <MuokkaaLisaaRaportointiPohja />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/raportointipohja/esikatselu"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.raporttipohja}
                                                >
                                                    <RaportointiPohjaEsikatselu />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route path="/login" element={<Login />} />
                                        <Route
                                            path="/rakenna-kysely"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.rakennaKysely}
                                                >
                                                    <RakennaKysely />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/esikatselu"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.esikatselu}
                                                >
                                                    <Esikatselu />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/aktivointi"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.aktivointi}
                                                >
                                                    <Aktivointi />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/lahetys"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.lahetys}
                                                >
                                                    <LahetysWithKey />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/tyontekijat-vardasta-lahetys/:kysymysryhmaId/:toimipaikkaOid"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.lahetys}
                                                >
                                                    <TyontekijatVardastaLahetys />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/yhteenveto"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.yhteenveto}
                                                >
                                                    <Yhteenveto />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/yhteenvedot"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.yhteenvetolist}
                                                >
                                                    <YhteenvetoList />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/arviointitulokset"
                                            element={
                                                <GuardedRoute
                                                    roles={allowedRoles.arviointitulokset}
                                                >
                                                    <Arviointitulokset />
                                                </GuardedRoute>
                                            }
                                        />
                                        <Route
                                            path="/error/:errorKey"
                                            element={<SimpleError />}
                                        />
                                    </Routes>
                                </main>
                            </Suspense>
                            <VirkailijaAlatunniste />
                        </div>
                    </Router>
                </div>
            </UserContext.Provider>
        </ThemeProvider>
    );
}

export default App;

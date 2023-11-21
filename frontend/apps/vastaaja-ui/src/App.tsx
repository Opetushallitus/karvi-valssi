import {Suspense, lazy, useEffect} from 'react';
import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import SnackBarAlert, {StickyAlert} from '@cscfi/shared/components/Alert/Alert';
import LoadingIndicator from '@cscfi/shared/components/Loading/LoadingIndicator';
import {ThemeProvider} from '@mui/material/styles';
import theme from '@cscfi/shared/theme';
import {useTranslation} from 'react-i18next';
import {vastauspalveluGetMessages$} from '@cscfi/shared/services/Vastauspalvelu-api/Vastauspalvelu-api-service';
import VastaajaNavigaatio from './components/Navigaatio/VastaajaNavigaatio';
import VastaajaAlatunniste from './components/Navigaatio/Alatunniste/VastaajaAlatunniste';

const VastaaKysely = lazy(() => import('./pages/VastaaKysely/VastaaKysely'));
const KiitosVastauksesta = lazy(
    () => import('./pages/KiitosVastauksesta/KiitosVastauksesta'),
);

function App() {
    const basename = process.env.NODE_ENV === 'test' ? '' : '/vastaaja-ui';
    const {
        i18n: {language: lang},
    } = useTranslation();

    useEffect(() => {
        document.documentElement.setAttribute('lang', lang);
    }, [lang]);

    useEffect(() => {
        vastauspalveluGetMessages$().subscribe();
    }, []);

    return (
        <ThemeProvider theme={theme}>
            <div className="app">
                <Router basename={basename}>
                    <StickyAlert />
                    <SnackBarAlert />
                    <div className="page-wrapper">
                        <VastaajaNavigaatio />
                        <Suspense fallback={<LoadingIndicator alwaysLoading />}>
                            <main className="content">
                                <LoadingIndicator />
                                <Routes>
                                    <Route path="/" element={<VastaaKysely />} />
                                    <Route
                                        path="/v/:vastaajatunnus"
                                        element={<VastaaKysely />}
                                    />
                                    <Route
                                        path="/kiitos"
                                        element={<KiitosVastauksesta />}
                                    />
                                </Routes>
                            </main>
                        </Suspense>
                        <VastaajaAlatunniste />
                    </div>
                </Router>
            </div>
        </ThemeProvider>
    );
}

export default App;

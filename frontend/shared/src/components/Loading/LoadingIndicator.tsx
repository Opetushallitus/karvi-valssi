import {useObservableState} from 'observable-hooks';
import Spinner from 'react-spinners/HashLoader';
import LoadingService from '../../services/Loading/Loading-service';
import styles from './LoadingIndicator.module.css';

interface LoadingIndicatorProps {
    alwaysLoading?: boolean;
}

function LoadingIndicator({alwaysLoading = false}: LoadingIndicatorProps) {
    const [isLoading] = useObservableState(() => LoadingService.isLoading$, false);
    return alwaysLoading || isLoading ? (
        <div className={styles.LoadingIndicator} data-testid="LoadingIndicator">
            <Spinner color="#4188b9" />
        </div>
    ) : null;
}

export default LoadingIndicator;

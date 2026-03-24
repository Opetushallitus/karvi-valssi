import {createContext} from 'react';
import {UserInfoType} from '@cscfi/shared/services/Login/Login-service';

export default createContext<UserInfoType | undefined>(undefined);
